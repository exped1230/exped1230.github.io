# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.

# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.

import argparse
import json
import os
import sys
from copy import deepcopy
from omegaconf import OmegaConf
from pathlib import Path
from typing import Callable, Iterable

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.utils import save_image
import torchsummary

import utils
import utils_img
import utils_model

sys.path.append('src')
from ldm.models.autoencoder import AutoencoderKL
from ldm.models.diffusion.ddpm import LatentDiffusion, DiffusionWrapper
from ldm.util import default
from loss.loss_provider import LossProvider

os.environ['CUDA_VISIBLE_DEVICES'] = '0,1,2,3,4,5'

def get_parser():
    parser = argparse.ArgumentParser()

    def aa(*args, **kwargs):
        group.add_argument(*args, **kwargs)

    group = parser.add_argument_group('Data parameters')
    aa("--train_dir", type=str, help="Path to the training data directory", required=True)
    aa("--val_dir", type=str, help="Path to the validation data directory", required=True)

    group = parser.add_argument_group('Model parameters')
    aa("--ldm_config", type=str, default="sd/stable-diffusion-v-1-4-original/v1-inference.yaml", help="Path to the configuration file for the LDM model") 
    aa("--ldm_ckpt", type=str, default="sd/stable-diffusion-v-1-4-original/sd-v1-4-full-ema.ckpt", help="Path to the checkpoint file for the LDM model") 
    aa("--msg_decoder_path", type=str, default= "/checkpoint/pfz/watermarking/models/hidden/dec_48b_whit.torchscript.pt", help="Path to the hidden decoder for the watermarking model")
    aa("--num_bits", type=int, default=48, help="Number of bits in the watermark")
    aa("--redundancy", type=int, default=1, help="Number of times the watermark is repeated to increase robustness")
    aa("--decoder_depth", type=int, default=8, help="Depth of the decoder in the watermarking model")
    aa("--decoder_channels", type=int, default=64, help="Number of channels in the decoder of the watermarking model")

    group = parser.add_argument_group('Training parameters')
    aa("--batch_size", type=int, default=4, help="Batch size for training")
    aa("--channels", type=int, default=3, help="Channels of the input images")
    aa("--img_size", type=int, default=256, help="Resize images to this size")
    aa("--scale_factor", type=int, default=8, help="Scale factor f for the original image")
    aa("--decay_factor", type=int, default=1, help="Scale factor f for the original image")
    aa("--loss_i", type=str, default="watson-vgg", help="Type of loss for the image loss. Can be watson-vgg, mse, watson-dft, etc.")
    aa("--loss_w", type=str, default="watson-vgg", help="Type of loss for the watermark loss. Can be watson-vgg, mse, watson-dft, etc")
    aa("--lambda_i", type=float, default=0.2, help="Weight of the image loss in the total loss")
    aa("--lambda_w", type=float, default=1.0, help="Weight of the watermark loss in the total loss")
    aa("--optimizer", type=str, default="AdamW,lr=5e-4", help="Optimizer and learning rate for training")
    aa("--steps", type=int, default=100, help="Number of steps to train the model for")
    aa("--warmup_steps", type=int, default=20, help="Number of warmup steps for the optimizer")
    aa("--local_rank", type=int, default=0, help="local device id on current node")
    # aa("--world_size", type=int, default=6, help="number of gpus")
    # aa("--init_method", default='tcp://127.0.0.1:3479', help="init-method")

    group = parser.add_argument_group('Logging and saving freq. parameters')
    aa("--log_freq", type=int, default=10, help="Logging frequency (in steps)")
    aa("--save_img_freq", type=int, default=1000, help="Frequency of saving generated images (in steps)")

    group = parser.add_argument_group('Experiments parameters')
    aa("--num_keys", type=int, default=1, help="Number of fine-tuned checkpoints to generate")
    aa("--num_keys_wm", type=int, default=1, help="Number of fine-tuned wm-checkpoints to generate")
    aa("--output_dir", type=str, default="output/", help="Output directory for logs and images (Default: /output)")
    aa("--seed", type=int, default=0)
    aa("--debug", type=utils.bool_inst, default=False, help="Debug mode")

    return parser

def main(params):

    # Set seeds for reproductibility 
    torch.manual_seed(params.seed)
    torch.cuda.manual_seed_all(params.seed)
    np.random.seed(params.seed)

    params.local_rank = int(os.environ["LOCAL_RANK"])
    torch.cuda.set_device(params.local_rank)
    device = torch.device('cuda', params.local_rank) if torch.cuda.is_available() else torch.device('cpu')
    # torch.distributed.init_process_group(backend="nccl", init_method=params.init_method, rank=params.local_rank, world_size=params.world_size)
    torch.distributed.init_process_group(backend="nccl")
    
    # Print the arguments
    # if params.local_rank == 0:
    #     print("__log__:{}".format(json.dumps(vars(params))))
    

    # Create the directories
    if not os.path.exists(params.output_dir):
        os.makedirs(params.output_dir)
    imgs_dir = os.path.join(params.output_dir, 'imgs')
    params.imgs_dir = imgs_dir
    if not os.path.exists(imgs_dir):
        os.makedirs(imgs_dir, exist_ok=True)

    # Loads LDM auto-encoder models
    if params.local_rank == 0:
        print(f'>>> Building LDM model with config {params.ldm_config} and weights from {params.ldm_ckpt}...')
    config = OmegaConf.load(f"{params.ldm_config}")

    ldm_full: LatentDiffusion = utils_model.load_model_from_config(config, params.ldm_ckpt)
    ldm_ae: AutoencoderKL = ldm_full.first_stage_model   #   
    ldm_ae.eval()
    ldm_ae.to(device)
    ldm_diffusion: DiffusionWrapper = ldm_full.model
    ldm_diffusion.eval()
    ldm_diffusion.to(device)
    
    
    # Loads hidden decoder
    if params.local_rank == 0:
        print(f'>>> Building hidden decoder with weights from {params.msg_decoder_path}...')
    if 'torchscript' in params.msg_decoder_path: 
        msg_decoder = torch.jit.load(params.msg_decoder_path).to(device)
        # already whitened
        
    else:
        msg_decoder = utils_model.get_hidden_decoder(num_bits=params.num_bits, redundancy=params.redundancy, num_blocks=params.decoder_depth, channels=params.decoder_channels).to(device)
        ckpt = utils_model.get_hidden_decoder_ckpt(params.msg_decoder_path)
        msg_decoder.eval()
        # whitening

    nbit = msg_decoder(torch.zeros(1, 3, 128, 128).to(device)).shape[-1]

    # Freeze LDM and hidden decoder
    for param in [*msg_decoder.parameters(), *ldm_ae.parameters()]:
        param.requires_grad = False

    # Loads the data
    # print(f'>>> Loading data from {params.train_dir} and {params.val_dir}...')
    vqgan_transform = transforms.Compose([
        transforms.Resize(params.img_size),
        transforms.CenterCrop(params.img_size),
        transforms.ToTensor(),
        utils_img.normalize_vqgan,
    ])
    train_sampler = torch.utils.data.distributed.DistributedSampler(params.train_dir)
    # train_loader = utils.get_dataloader(params.train_dir, vqgan_transform, params.batch_size, num_imgs=params.batch_size*params.steps, shuffle=True, num_workers=4, collate_fn=None)
    train_loader = utils.get_dataloader_parallel(params.train_dir, vqgan_transform, params.batch_size, num_imgs=params.batch_size*params.steps, shuffle=(train_sampler is None), sampler=train_sampler, num_workers=4, collate_fn=None)
    val_loader = utils.get_dataloader(params.val_dir, vqgan_transform, params.batch_size*4, num_imgs=1000, shuffle=False, num_workers=4, collate_fn=None)
    vqgan_to_imnet = transforms.Compose([utils_img.unnormalize_vqgan, utils_img.normalize_img])
    
    for ii_key in range(params.num_keys_wm):

        # Creating key_wm
        wm_size = (params.channels, params.img_size, params.img_size)
        if params.local_rank == 0:
            print(f'\n>>> Creating key_wm with size is {wm_size}...')
        key_wm = default(key_wm, lambda: torch.randn(wm_size)) # 3 256 256

        # Copy the LDM decoder and finetune the copy
        ldm_decoder = deepcopy(ldm_ae)
        ldm_decoder.encoder = nn.Identity()
        ldm_decoder.quant_conv = nn.Identity()
        lwm_decoder = deepcopy(ldm_decoder)
        # ldm_decoder.to(device)
        for param in ldm_decoder.parameters():
            param.requires_grad = True
        for param in lwm_decoder.parameters():
            param.requires_grad = True
        ldm_decoder = nn.parallel.DistributedDataParallel(ldm_decoder.to(device), device_ids=[params.local_rank], find_unused_parameters=True)
        lwm_decoder = nn.parallel.DistributedDataParallel(lwm_decoder.to(device), device_ids=[params.local_rank], find_unused_parameters=True)
        optim_params = utils.parse_params(params.optimizer)
        optimizer_id = utils.build_optimizer(model_params=ldm_decoder.parameters(), **optim_params)
        optimizer_wd = utils.build_optimizer(model_params=lwm_decoder.parameters(), **optim_params)

        # Training loop
        if params.local_rank == 0:
            print(f'>>> Training...')

        train_stats = train(train_loader, optimizer_id, optimizer_wd, ldm_ae, ldm_diffusion, ldm_decoder, lwm_decoder, vqgan_to_imnet, key_wm, params)
        val_stats = val(val_loader, ldm_ae, ldm_diffusion, ldm_decoder, lwm_decoder, vqgan_to_imnet, key_wm, params)
        log_stats = {'key': key_str,
                **{f'train_{k}': v for k, v in train_stats.items()},
                **{f'val_{k}': v for k, v in val_stats.items()},
            }
        save_dict = {
            'ldm_decoder': ldm_decoder.state_dict(),
            'lwm_decoder': lwm_decoder.state_dict(),
            'optimizer_id': optimizer_id.state_dict(),
            'optimizer_wd': optimizer_wd.state_dict(),
            'params': params,
        }
        
        # Save checkpoint
        if params.local_rank == 0:
            torch.save(save_dict, os.path.join(params.output_dir, f"checkpoint_{ii_key:03d}.pth"))
        with (Path(params.output_dir) / "log.txt").open("a") as f:
            f.write(json.dumps(log_stats) + "\n")
        with (Path(params.output_dir) / "keys.txt").open("a") as f:
            f.write(os.path.join(params.output_dir, f"checkpoint_{ii_key:03d}.pth") + "\t" + key_str + "\n")
        print('\n')

def train(data_loader: Iterable, optimizer_id: torch.optim.Optimizer, optimizer_wd: torch.optim.Optimizer, ldm_ae: AutoencoderKL, ldm_diffusion: DiffusionWrapper, ldm_decoder:AutoencoderKL, lwm_decoder:AutoencoderKL, vqgan_to_imnet:nn.Module, key_wm: torch.Tensor, params: argparse.Namespace):
    header = 'Train'
    metric_logger = utils.MetricLogger(delimiter="  ")
    # ldm_decoder.decoder.train()
    ldm_decoder.module.decoder.train()
    lwm_decoder.module.decoder.train()
    base_lr_id = optimizer_id.param_groups[0]["lr"]
    base_lr_wd = optimizer_wd.param_groups[0]["lr"]
    # 同步屏障：等待所有分布式进程结束后才能开始开始训练
    torch.distributed.barrier()
    for ii, imgs in enumerate(metric_logger.log_every(data_loader, params.log_freq, header)):
        imgs = imgs.cuda(params.local_rank) # 4 3 256 256
        keys_wm = key_wm.repeat(imgs.shape[0], 1) # 3 256 256 -> 4 3 256 256
        
        utils.adjust_learning_rate(optimizer_id, ii, params.steps, params.warmup_steps, base_lr)
        utils.adjust_learning_rate(optimizer_wd, ii, params.steps, params.warmup_steps, base_lr)
        # encode images
        imgs_z = ldm_ae.encode(imgs) # b c h w -> b z h/f w/f
        imgs_z = imgs_z.mode()

        # encode watermark
        wm_z = ldm_ae.encode(keys_wm) # 4 3 256 256 ->  4 4 32 32
        wm_z = wm_z.mode()

        mix_z = imgs_z + params.decay_factor * wm_z

        # diffusion process with watermark interpolation
        mix_z_out = ldm_diffusion(mix_z) 

        # decode the watermarking latents with finetuned two decoders
        imgs_i = ldm_decoder.module.decode(mix_z_out) # b z h/f w/f -> b c h w
        imgs_w = lwm_decoder.module.decode(mix_z_out) # b z h/f w/f -> b c h w

        # compute loss
        lossw = compute_loss(params.loss_w, imgs_w, keys_wm)
        lossi = compute_loss(params.loss_i, imgs_i, imgs)
        loss = params.lambda_w * lossw + params.lambda_i * lossi

        # optim step
        loss.backward()
        optimizer_id.step()
        optimizer_wd.step()
        optimizer_id.zero_grad()
        optimizer_wd.zero_grad()

        # log stats
        # diff = (~torch.logical_xor(decoded>0, keys>0)) # b k -> b k
        # bit_accs = torch.sum(diff, dim=-1) / diff.shape[-1] # b k -> b
        # word_accs = (bit_accs == 1) # b
        log_stats = {
            "iteration": ii,
            "loss": loss.item(),
            "loss_w": lossw.item(),
            "loss_i": lossi.item(),
            "psnr": utils_img.psnr(imgs_i, imgs).mean().item(),
            "psnr_wm": utils_img.psnr(imgs_w, keys_wm).mean().item(),
            # "bit_acc_avg": torch.mean(bit_accs).item(),
            # "word_acc_avg": torch.mean(word_accs.type(torch.float)).item(),
            "lr_i": optimizer_id.param_groups[0]["lr"],
            "lr_w": optimizer_wd.param_groups[0]["lr"],
        }
        for name, loss in log_stats.items():
            metric_logger.update(**{name:loss})
        if ii % params.log_freq == 0:
            print(json.dumps(log_stats))
        
        # save images during training
        if ii % params.save_img_freq == 0:
            save_image(torch.clamp(utils_img.unnormalize_vqgan(imgs),0,1), os.path.join(params.imgs_dir, f'{ii:03}_train_orig.png'), nrow=8)
            save_image(torch.clamp(utils_img.unnormalize_vqgan(imgs_d0),0,1), os.path.join(params.imgs_dir, f'{ii:03}_train_d0.png'), nrow=8)
            save_image(torch.clamp(utils_img.unnormalize_vqgan(imgs_w),0,1), os.path.join(params.imgs_dir, f'{ii:03}_train_w.png'), nrow=8)
    
    print("Averaged {} stats:".format('train'), metric_logger)
    return {k: meter.global_avg for k, meter in metric_logger.meters.items()}

@torch.no_grad()
def val(data_loader: Iterable, ldm_ae: AutoencoderKL, ldm_diffusion: DiffusionWrapper, ldm_decoder: AutoencoderKL, lwm_decoder: AutoencoderKL, vqgan_to_imnet:nn.Module, key_wm: torch.Tensor, params: argparse.Namespace):
    header = 'Eval'
    metric_logger = utils.MetricLogger(delimiter="  ")
    ldm_decoder.module.decoder.eval()
    lwm_decoder.module.decoder.eval()
    for ii, imgs in enumerate(metric_logger.log_every(data_loader, params.log_freq, header)):
        imgs = imgs.cuda(params.local_rank) # 4 3 256 256
        keys_wm = key_wm.repeat(imgs.shape[0], 1) # 3 256 256 -> 4 3 256 256
        
        utils.adjust_learning_rate(optimizer_id, ii, params.steps, params.warmup_steps, base_lr)
        utils.adjust_learning_rate(optimizer_wd, ii, params.steps, params.warmup_steps, base_lr)
        # encode images
        imgs_z = ldm_ae.encode(imgs) # b c h w -> b z h/f w/f
        imgs_z = imgs_z.mode()

        # encode watermark
        wm_z = ldm_ae.encode(keys_wm) # 4 3 256 256 ->  4 4 32 32
        wm_z = wm_z.mode()

        mix_z = imgs_z + params.decay_factor * wm_z

        # diffusion process with watermark interpolation
        mix_z_out = ldm_diffusion(mix_z) 

        # decode the watermarking latents with finetuned two decoders
        imgs_i = ldm_decoder.module.decode(mix_z_out) # b z h/f w/f -> b c h w
        imgs_w = lwm_decoder.module.decode(mix_z_out) # b z h/f w/f -> b c h w

        log_stats = {
            "iteration": ii,
            "psnr": utils_img.psnr(imgs_i, imgs).mean().item(),
            "psnr-wm": utils_img.psnr(imgs_w, keys_wm).mean().item(),
        }
        attacks = {
            'none': lambda x: x,
            'crop_01': lambda x: utils_img.center_crop(x, 0.1),
            'crop_05': lambda x: utils_img.center_crop(x, 0.5),
            'rot_25': lambda x: utils_img.rotate(x, 25),
            'rot_90': lambda x: utils_img.rotate(x, 90),
            'resize_03': lambda x: utils_img.resize(x, 0.3),
            'resize_07': lambda x: utils_img.resize(x, 0.7),
            'brightness_1p5': lambda x: utils_img.adjust_brightness(x, 1.5),
            'brightness_2': lambda x: utils_img.adjust_brightness(x, 2),
            'jpeg_80': lambda x: utils_img.jpeg_compress(x, 80),
            'jpeg_50': lambda x: utils_img.jpeg_compress(x, 50),
        }
        for name, attack in attacks.items():
            imgs_aug = attack(vqgan_to_imnet(imgs_i))
            imgs_w = lwm_decoder.module.decode(imgs_aug) # b c h w -> b k
            log_stats[f'psnr_{name}'] = utils_img.psnr(imgs_i, imgs).mean().item(),
            log_stats[f'psnr_wm_{name}'] = utils_img.psnr(imgs_w, keys_wm).mean().item(),
        for name, loss in log_stats.items():
            metric_logger.update(**{name:loss})

        if ii % params.save_img_freq == 0:
            save_image(torch.clamp(utils_img.unnormalize_vqgan(imgs),0,1), os.path.join(params.imgs_dir, f'{ii:03}_val_orig.png'), nrow=8)
            save_image(torch.clamp(utils_img.unnormalize_vqgan(imgs_d0),0,1), os.path.join(params.imgs_dir, f'{ii:03}_val_d0.png'), nrow=8)
            save_image(torch.clamp(utils_img.unnormalize_vqgan(imgs_w),0,1), os.path.join(params.imgs_dir, f'{ii:03}_val_w.png'), nrow=8)
    
    print("Averaged {} stats:".format('eval'), metric_logger)
    return {k: meter.global_avg for k, meter in metric_logger.meters.items()}

def compute_loss(loss_type:str, predicted, reference):
    if loss_type == 'mse':
        loss = torch.mean((predicted - reference)**2)
    elif loss_type == 'watson-dft':
        provider = LossProvider()
        loss_percep = provider.get_loss_function('Watson-DFT', colorspace='RGB', pretrained=True, reduction='sum')
        loss_percep = loss_percep.to(device)
        loss = loss_percep((1+predicted)/2.0, (1+reference)/2.0)/ predicted[0]
    elif loss_type == 'watson-vgg':
        provider = LossProvider()
        loss_percep = provider.get_loss_function('Watson-VGG', colorspace='RGB', pretrained=True, reduction='sum')
        loss_percep = loss_percep.to(device)
        loss = loss_percep((1+predicted)/2.0, (1+reference)/2.0)/ predicted.shape[0]
    elif loss_type == 'ssim':
        provider = LossProvider()
        loss_percep = provider.get_loss_function('SSIM', colorspace='RGB', pretrained=True, reduction='sum')
        loss_percep = loss_percep.to(device)
        loss = loss_percep((1+predicted)/2.0, (1+reference)/2.0)/ predicted.shape[0]
    else:
        raise NotImplementedError
    return loss

if __name__ == '__main__':

    # generate parser / parse parameters
    parser = get_parser()
    params = parser.parse_args()

    # run experiment
    main(params)
