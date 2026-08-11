# Telegram Kalori Botu

Serbest metinle yazılan malzemelerden kalori/makro hesaplayan, Claude API
kullanan basit bir Telegram botu.

## 1. Telegram bot token'ı al
1. Telegram'da **@BotFather**'a git.
2. `/newbot` yaz, adını ve kullanıcı adını belirle.
3. Sana verdiği token'ı kopyala (örn. `123456:ABC-DEF...`).

## 2. Anthropic API key al
[console.anthropic.com](https://console.anthropic.com) üzerinden bir API key oluştur.
Not: Bu ücretsiz değildir ama Haiku modeliyle bu boyutta bir kullanım çok düşük maliyetlidir.

## 3. Kurulum

```bash
cd telegram_kalori_bot
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

`.env` dosyasını açıp kendi token/key'lerini yapıştır.

## 4. Testleri çalıştır (opsiyonel ama önerilir)

```bash
pytest -v
```

## 5. Botu çalıştır

```bash
python main.py
```

Telegram'da botuna git, `/start` yaz, sonra örneğin:

```
200 gram tavuk göğsü, 1 su bardağı pirinç, 4 kişiye böl
```

Porsiyon sayısını yazmazsan bot soracak. Sonuç geldikten sonra
`değerlendir` yazarsan öğünü kısaca değerlendirir.

Telegram'da `/bugun` yazarsan kaydettiğin öğünlerin toplamını görürsün.

## Sonraki adımlar (opsiyonel)
- **Deployment (Render / Fly.io)**: `run_polling()` yerine webhook moduna
  geçmek gerekir (ücretsiz planlarda genelde polling de çalışır, ama
  webhook daha "production" bir yaklaşımdır — CV'de bahsetmeye değer).
- **Rate limiting / hata mesajları**: Claude API'den hatalı/timeout
  cevap geldiğinde kullanıcıya daha açıklayıcı mesaj gösterme.
