#!/usr/bin/env python3
"""
Тестовый скрипт для проверки генерации шаблонов объявлений Allegro с OpenAI
"""

import json
import os
from dotenv import load_dotenv
from allegro import (
    generate_allegro_listing_template, 
    create_full_allegro_listing,
    generate_openai_description,
    generate_openai_parameters,
    generate_openai_tags
)

# Загружаем переменные окружения
load_dotenv()

def test_openai_integration():
    """Тестирует интеграцию с OpenAI"""
    
    # Проверяем наличие API ключа
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY не найден в .env файле")
        print("Добавьте OPENAI_API_KEY=your_api_key в файл .env")
        return False
    
    print("✅ OPENAI_API_KEY найден")
    
    # Тестовые данные товара
    test_product = {
        'name': 'iPhone 13 Pro 128GB Czarny',
        'price': '4,299.00 zł',
        'url': 'https://allegro.pl/oferta/iphone-13-pro-128gb-czarny',
        'image': 'https://via.placeholder.com/300x200',
        'description': 'Nowy iPhone 13 Pro'
    }
    
    print("\n🔍 Тестируем генерацию описания с OpenAI...")
    try:
        description = generate_openai_description(test_product['name'], test_product['price'])
        print(f"✅ Описание сгенерировано ({len(description)} символов)")
        print(f"📝 Начало описания: {description[:100]}...")
    except Exception as e:
        print(f"❌ Ошибка генерации описания: {e}")
        return False
    
    print("\n🔍 Тестируем генерацию параметров с OpenAI...")
    try:
        parameters = generate_openai_parameters(test_product['name'])
        print(f"✅ Параметры сгенерированы: {len(parameters)} параметров")
        for key, value in list(parameters.items())[:3]:
            print(f"   {key}: {value}")
    except Exception as e:
        print(f"❌ Ошибка генерации параметров: {e}")
        return False
    
    print("\n🔍 Тестируем генерацию тегов с OpenAI...")
    try:
        tags = generate_openai_tags(test_product['name'])
        print(f"✅ Теги сгенерированы: {len(tags)} тегов")
        print(f"   Теги: {', '.join(tags[:5])}...")
    except Exception as e:
        print(f"❌ Ошибка генерации тегов: {e}")
        return False
    
    print("\n🔍 Тестируем генерацию полного шаблона с OpenAI...")
    try:
        template = create_full_allegro_listing(test_product, use_openai=True)
        print(f"✅ Полный шаблон сгенерирован")
        print(f"   Заголовок: {template['title']}")
        print(f"   Категория: {template['category']}")
        print(f"   Тегов: {len(template['tags'])}")
        print(f"   С OpenAI: {template.get('generated_with_openai', False)}")
    except Exception as e:
        print(f"❌ Ошибка генерации шаблона: {e}")
        return False
    
    return True

def test_batch_generation():
    """Тестирует пакетную генерацию"""
    
    test_products = [
        {
            'name': 'Samsung Galaxy S21 128GB Phantom Black',
            'price': '2,999.00 zł',
            'url': '',
            'image': '',
            'description': ''
        },
        {
            'name': 'MacBook Air M2 13" 256GB Space Gray',
            'price': '5,999.00 zł',
            'url': '',
            'image': '',
            'description': ''
        },
        {
            'name': 'Sony WH-1000XM4 Słuchawki Bezprzewodowe',
            'price': '1,299.00 zł',
            'url': '',
            'image': '',
            'description': ''
        }
    ]
    
    print("\n🔍 Тестируем пакетную генерацию...")
    
    templates = []
    for i, product in enumerate(test_products):
        try:
            template = generate_allegro_listing_template(product, use_openai=True)
            templates.append({
                'index': i,
                'product_name': product['name'],
                'template': template,
                'success': True
            })
            print(f"✅ Шаблон {i+1} сгенерирован: {product['name'][:30]}...")
        except Exception as e:
            templates.append({
                'index': i,
                'product_name': product['name'],
                'error': str(e),
                'success': False
            })
            print(f"❌ Ошибка шаблона {i+1}: {e}")
    
    successful = len([t for t in templates if t['success']])
    print(f"\n📊 Результаты пакетной генерации:")
    print(f"   Всего: {len(templates)}")
    print(f"   Успешно: {successful}")
    print(f"   Ошибок: {len(templates) - successful}")
    
    return successful == len(templates)

def save_test_results():
    """Сохраняет тестовые результаты в файл"""
    
    test_product = {
        'name': 'iPhone 13 Pro 128GB Czarny',
        'price': '4,299.00 zł',
        'url': 'https://allegro.pl/oferta/iphone-13-pro-128gb-czarny',
        'image': 'https://via.placeholder.com/300x200',
        'description': 'Nowy iPhone 13 Pro'
    }
    
    try:
        # Генерируем шаблоны с OpenAI и без
        template_with_openai = create_full_allegro_listing(test_product, use_openai=True)
        template_without_openai = create_full_allegro_listing(test_product, use_openai=False)
        
        # Сохраняем результаты
        results = {
            'test_product': test_product,
            'template_with_openai': template_with_openai,
            'template_without_openai': template_without_openai,
            'comparison': {
                'description_length_openai': len(template_with_openai['description']),
                'description_length_fallback': len(template_without_openai['description']),
                'parameters_count_openai': len(template_with_openai['parameters']),
                'parameters_count_fallback': len(template_without_openai['parameters']),
                'tags_count_openai': len(template_with_openai['tags']),
                'tags_count_fallback': len(template_without_openai['tags'])
            }
        }
        
        with open('test_openai_results.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print("\n💾 Тестовые результаты сохранены в test_openai_results.json")
        
        # Показываем сравнение
        comp = results['comparison']
        print(f"\n📊 Сравнение результатов:")
        print(f"   Описание (OpenAI): {comp['description_length_openai']} символов")
        print(f"   Описание (Fallback): {comp['description_length_fallback']} символов")
        print(f"   Параметры (OpenAI): {comp['parameters_count_openai']}")
        print(f"   Параметры (Fallback): {comp['parameters_count_fallback']}")
        print(f"   Теги (OpenAI): {comp['tags_count_openai']}")
        print(f"   Теги (Fallback): {comp['tags_count_fallback']}")
        
    except Exception as e:
        print(f"❌ Ошибка сохранения результатов: {e}")

if __name__ == "__main__":
    print("🚀 Тестирование интеграции с OpenAI для генерации шаблонов Allegro")
    print("=" * 70)
    
    # Тестируем интеграцию
    if test_openai_integration():
        print("\n✅ Все тесты интеграции прошли успешно!")
        
        # Тестируем пакетную генерацию
        if test_batch_generation():
            print("\n✅ Пакетная генерация работает корректно!")
        else:
            print("\n⚠️ Пакетная генерация имеет проблемы")
        
        # Сохраняем тестовые результаты
        save_test_results()
        
    else:
        print("\n❌ Тесты интеграции не прошли")
        print("Проверьте настройки OpenAI API") 