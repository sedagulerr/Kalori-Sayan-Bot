"""
Claude API ile iletisim katmani.
- parse_meal: serbest metni yapilandirilmis malzeme/kalori listesine cevirir (tool use)
- get_meal_assessment: hesaplanan toplamlara gore kisa bir ogun degerlendirmesi yazdirir
"""

import os
from anthropic import Anthropic

client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# Bu is icin Haiku hizli ve ucuz, yeterli kalite sagliyor.
# Daha tutarli/detayli sonuc istersen "claude-sonnet-5" ile degistirebilirsin.
MODEL = "claude-haiku-4-5-20251001"

MEAL_TOOL = {
    "name": "kaydet_yemek_bilgisi",
    "description": (
        "Kullanicinin tarif ettigi yemek malzemelerinin tahmini kalori ve "
        "makro besin degerlerini kaydeder. Metinde gercekten yiyecek/malzeme "
        "gecmiyorsa (selamlasma, tek basina bir sayi, alakasiz bir komut vb.) "
        "ingredients alanini BOS DIZI olarak birak. Metinde gecmeyen hicbir "
        "malzemeyi uydurma."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "ingredients": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string", "description": "Malzeme adi"},
                        "amount_description": {
                            "type": "string",
                            "description": "Miktar, oldugu gibi (orn. '200 gram', '1 su bardagi')",
                        },
                        "calories": {"type": "number"},
                        "protein_g": {"type": "number"},
                        "carbs_g": {"type": "number"},
                        "fat_g": {"type": "number"},
                    },
                    "required": [
                        "name",
                        "amount_description",
                        "calories",
                        "protein_g",
                        "carbs_g",
                        "fat_g",
                    ],
                },
            },
            "portion_count": {
                "type": ["integer", "null"],
                "description": (
                    "SADECE kullanici acikca bir porsiyon/kisi sayisi belirtmisse "
                    "doldur (orn. '4 kisiye bol', '3 porsiyon', 'tek kisilik'). "
                    "Kullanici hicbir sayi/porsiyon belirtmemisse KESINLIKLE null "
                    "birak - varsayilan olarak 1 yazma, tahmin etme."
                ),
            },
        },
        "required": ["ingredients", "portion_count"],
    },
}


def parse_meal(text: str) -> dict:
    """Serbest metni Claude'a gonderip yapilandirilmis malzeme/kalori verisi alir."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        tools=[MEAL_TOOL],
        tool_choice={"type": "tool", "name": "kaydet_yemek_bilgisi"},
        messages=[
            {
                "role": "user",
                "content": (
                    "Asagidaki metni analiz et. Eger metin gercekten yemek/"
                    "malzeme icermiyorsa (selamlasma, alakasiz bir cumle, tek "
                    "basina bir sayi/komut vb.) ingredients alanini bos dizi "
                    "([]) olarak birak - metinde gecmeyen hicbir malzemeyi "
                    "UYDURMA. Metin gercekten yemek iceriyorsa, her malzeme "
                    "icin gercekci, standart beslenme veritabanlarina (USDA "
                    "vb.) yakin kalori ve makro (protein/karbonhidrat/yag) "
                    "tahmini yap. portion_count alanini SADECE kullanici acikca "
                    "bir sayi/porsiyon belirtmisse doldur, aksi halde null "
                    "birak - asla varsayilan olarak 1 yazma.\n\n"
                    f'Metin: "{text}"'
                ),
            }
        ],
    )
    for block in response.content:
        if block.type == "tool_use":
            return block.input
    raise ValueError("Claude'dan yapilandirilmis cevap alinamadi")


def get_meal_assessment(
    ingredients: list,
    totals: dict,
    portion_totals: dict | None,
    meal_type: str | None = None,
) -> str:
    """Hesaplanmis toplamlara ve (varsa) ogun turune gore kisa bir degerlendirme uretir."""
    ingredient_lines = "\n".join(
        f"- {i['name']} ({i['amount_description']}): {i['calories']} kcal"
        for i in ingredients
    )
    per_person_line = f"\nKisi basi: {portion_totals}" if portion_totals else ""
    meal_type_line = f"\nOgun turu: {meal_type}" if meal_type else ""

    prompt = (
        "Asagidaki ogunu kisa ve net sekilde degerlendir (3-4 cumle, Turkce). "
        "Ogun turu belirtilmisse (kahvalti/ogle yemegi/aksam yemegi/atistirmalik) "
        "bunu dikkate alarak degerlendir - ornegin atistirmalik icin farkli bir "
        "beklenti olur, ana ogun icin farkli. Protein/karbonhidrat/yag dengesine "
        "ve ogunun o ogun turu icin uygun olup olmadigina deg, varsa 1 kisa "
        "oneri ver. Genel gecer bir dil kullan, tibbi tavsiye verme. Duz metin "
        "yaz: markdown, baslik (#), yildizli kalin yazi (**) veya liste "
        "isareti kullanma.\n\n"
        f"Malzemeler:\n{ingredient_lines}\n\nToplam: {totals}{per_person_line}{meal_type_line}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.content[0].text
