# Anonim Bot

Telegram uchun anonim xabarlar yuborish boti. Foydalanuvchilar bir-birlariga anonim tarzda xabar, media fayllar yuborishlari mumkin.

## Xususiyatlar

- Anonim xabar yuborish
- Media fayllari yuborish (video, audio, voice)
- Token tizimi
- Referal tizimi
- Premium ta'rif

## O'rnatish

1. Repositoriyani clone qiling:
```bash
git clone https://github.com/abdulloh1001/anonbot.git
cd anonbot
```

2. Kerakli kutubxonalarni o'rnating:
```bash
pip install -r requirements.txt
```

3. `.env` faylini yarating va bot tokenini qo'ying:
```
BOT_TOKEN=your_bot_token_here
LOG_CHANNEL=-100123456789
REF_REWARD=5
PHOTO_TOKEN_THRESHOLD=50
```

4. Botni ishga tushiring:
```bash
python main.py
```

## Railway'da ishga tushirish

1. Railway proektini yarating
2. GitHub repositoriyangizni ulang
3. Environment Variables bo'limida quyidagi o'zgaruvchilarni qo'shing:
   - `BOT_TOKEN`
   - `LOG_CHANNEL`
   - `REF_REWARD`
   - `PHOTO_TOKEN_THRESHOLD`
4. Deploy qiling

## Litsenziya

MIT