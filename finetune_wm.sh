torchrun --nnodes=1 --nproc-per-node=6 finetune_lwm_decoders.py \
    --ldm_config /root/zyma/diffusion/stable_signature/configs/sd/v1-inference.yaml \
    --ldm_ckpt /root/zyma/models/Stable_Diffusion/sd-v14-original/sd-v1-4-full-ema.ckpt \
    --msg_decoder_path /root/zyma/models/Stable_Signature/another/dec_48b_whit.torchscript.pt \
    --train_dir /root/zyma/datasets/MSCOCO/coco2017/train/data \
    --val_dir /root/zyma/datasets/MSCOCO/coco2017/validation/data
    