"""
Парсинг сайта объявлений о продаже квартир 167000.ru
"""
from bs4 import BeautifulSoup as soup
from dateutil.parser import parse as date_parser
from datetime import datetime
from datetime import date
from io import BytesIO
from PIL import Image
from psycopg2.extensions import adapt
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from random import randint

import base64
import configparser
import copy
import os
import psycopg2
import psycopg2.extras
import re
import sys
import time
import uuid

import lib_market
from vilogger import ViLogger

class MarketResearch167000():
    def __init__(self):
        config = configparser.ConfigParser()
        config.read('main.ini')
        current_date = date.today().strftime('%Y%m%d')
        self._log = ViLogger(f'{current_date}_main.log', 0, 20)
        db_host = config.get('db', 'dbhost')
        db_name = config.get('db', 'dbname')
        db_user = config.get('db', 'dbuser')
        db_pwrd = config.get('db', 'dbpwrd')
        self._SCRSHOT_PATH = config.get('screenshot', 'SCRSHOT_PATH')
        self._SCRSHOT_WIDTH = config.getint('screenshot', 'SCRSHOT_WIDTH')
        self._SCRSHOT_HEIGHT = config.getint('screenshot', 'SCRSHOT_HEIGHT')
        self._SCRSHOT_USE_JPG = config.get('screenshot', 'SCRSHOT_USE_JPG')
        self._SCRSHOT_QUAL = config.getint('screenshot', 'SCRSHOT_QUAL')
        self._base_url = config.get('url', 'base_url')
        chrome_service = Service(config.get('common', 'driver'))
        chrome_options = Options()
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-certificate-errors-spki-list')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--start-maximized')
        chrome_options.add_argument('--start-fullscreen')
        self._chrome_driver =  webdriver.Chrome(service=chrome_service, options=chrome_options)
        try:    
            self._db_connection = psycopg2.connect(dbname=db_name, user=db_user, password=db_pwrd, host=db_host)
        except:
            self._log.print_log('Не удалось установить соединение с базой данных.', self._log.ERROR)
        self._offer_ids = list()
        self._all_offers_characteristics = list()
        self._parsed_ids_and_prices = {}
    
    def __del__(self):
        self._chrome_driver.quit()
        self._db_connection.close()

    def get_all_offer_ids(self) -> None:
        """
        Собирает ID и цены всех предожений, которые есть на всех страницах и удаляет повторяющиеся.
        
        Аргументы:      page_url - URL страницы с предложениями. 
        Возвращает:     Список с ID предложений сайта без повторов.  
        """
        tmp_offer_ids = []
        tmp_offer_prices = []
        self._log.print_log(f'Дата парсинга: {date.today()}')
        self._log.print_log('Начинаем сбор всех ID и цен объектов, которые есть на страницах поиска.')
        for page in range(self._get_last_page()):
            time.sleep(randint(10,15))
            page_soup = self._get_url_soup(f'{self._base_url}?page={page+1}')
            tmp_offer_ids += self._get_page_offer_ids (page_soup)
            tmp_offer_prices += self._get_page_offer_prices (page_soup)
        for i in range(0, len(tmp_offer_ids)):
            self._parsed_ids_and_prices[tmp_offer_ids[i]] = tmp_offer_prices[i]
        self._remove_offer_duplicates()
        if len(self._offer_ids) == 0:
            self._log.print_log('Нет новых объявлений на 167000.ru')
        else:
            self._log.print_log('Обнаружены новые объявления для парсинга на 167000.ru')
            self._log.print_log(f'Объявлений на парсинг: {len(self._offer_ids)}')

    def get_all_characteristics(self) -> list:
        """
        Для каждого найденного ID предложения собирает его характеристики и собирает все характеристики каждого предложения в список кортежей.
        
        Аргументы:      - 
        Возвращает:     -
        """
        self._log.print_log('Начинаем парсинг характеристик всех найденных объектов')
        for id in self._offer_ids:
            self._all_offers_characteristics.append(self._get_offer_characteristics(id))
        if len(self._all_offers_characteristics) > 0:
            self._log.print_log(f'Собраны характеристики всех объектов. Количество квартир: {len(self._all_offers_characteristics)}')

    def save_data (self) -> None:
        """
        Полученные характеристики всех объектов записывает в БД таблицу t_offers_tmp.

        Аргументы: -
        Возвращает: -
        """  
        try:      
            table_columns = (
                '(offer_tmp_id, offer_id, offer_url, offer_screenshot_path, offer_start_date, ' +
                'offer_stop_date, address, price, rooms_total, total_area, flat_floor, total_floors, walls_type, ' +
                'renovation_type, construction_year, offer_description, offer_seller, phone_numbers)'
            )
            cursor = self._db_connection.cursor()
            sql_str: str = f'INSERT INTO t_offers_tmp {table_columns} VALUES %s;'
            psycopg2.extras.execute_values(
                cursor, sql_str, self._all_offers_characteristics, template=None, page_size=100)
            self._db_connection.commit()
            cursor.close()
            if len(self._all_offers_characteristics) > 0:
                self._log.print_log(f'Данные успешно импортированы в базу данных.')
        except:
            self._log.print_log(f'Сбой при импорте объявлений в базу данных.', self._log.ERROR)

    def _get_last_page(self) -> int:
        """
        Ищет число страниц со списком предложений в soup-объекте. 

        Аргументы: -
        Возвращает:     Число страниц с предложениями, тип int.
        """
        page_soup = self._get_url_soup(self._base_url)
        pages_list = [int(tag.string)
                    for tag in page_soup.find_all('a', {'class': 'paginator__item _link'}) if tag]
        if len(pages_list) != 0:
            return max(pages_list)
        else:
            return 1

    def _get_url_soup (self, page_url: str) -> soup:
        """
        Получает объект soup со страницы по её URL. 
            
        Аргументы
            page_url       URL страницы, тип str
        """
        try:
            self._chrome_driver.get(page_url)
            return soup(self._chrome_driver.page_source, features='lxml')
        except:
            self._log.print_log('Неизвестная ошибка при получении соупа страницы по URL', self._log.ERROR)

    def _get_offer_construction_year (self, offer_soup: soup) -> int:
        """
        Находит год постройки дома квартиры из объявления.
           
        Аргументы:          offer_soup - Soup-объект страницы с предложением.
        Возвращает:         Год постройки дома в формате int.
        """
        try:
            return int(offer_soup.find('table', {'class': 'details'}).find('th', text=re.compile(r'Год постройки')).next_sibling.string)
        except AttributeError:
            return None
        except:
            self._log.print_log('Неизвестная ошибка при парсинге года постройки дома', self._log.ERROR)
        return None
    
    def _get_offer_date (self, offer_soup: soup) -> datetime:
        """
        Находит дату публикации объявления.
           
        Аргументы:          offer_soup - Soup-объект страницы с предложением.
        Возвращает:         Дату публикации предложения в формате datetime.
        """
        try:
            return datetime.strptime(offer_soup.find('div', {'class': 'info flex-row'}).find_all('b')[1].text, '%d.%m.%Y %H:%M') 
        except AttributeError:
            self._log.print_log('Ошибка атрибута при сборе даты публикации объявления', self._log.ERROR)
        except TypeError:
            self._log.print_log('Нет возможности преобразовать строку в дату при сборе даты публикации объявления', self._log.ERROR)
        except:
            self._log.print_log('Неизвестная ошибка при сборе даты публикации объявления', self._log.ERROR)
        return None

    def _get_offer_description (self, offer_soup: soup) -> str:
        """
        Парсит описание предложения, очищает текст от emoji, очищает текст от escape-последовательностей и прочих символов.

        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Очищенный текст предложения типа str. 
        """
        try:
            description = offer_soup.find('tr', {'class': 'comment'})
            if description:
                description = ' '.join([paragraph.text for paragraph in description.find_all('p')])
                return lib_market.clean_text(description)
            else:
                return None
        except AttributeError:
            self._log.print_log ('Не удалось найти тег в соупе при получении описания предложения', self._log.ERROR)
        except TypeError:
            self._log.print_log ('Ошибка при преобразовании отфильтрованного soup в текст', self._log.ERROR)
        except:
            self._log.print_log ('Неизвестная ошибка при получении описания предложения', self._log.ERROR)
        return None

    def _get_offer_floors_info (self, offer_soup: soup) -> list:
        """
        Парсит информацию об этаже квартиры и этажности всего здания. 
        
        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Список вида: [этаж квартиры, этажность здания]
        """
        try:
            return re.findall(r'\d+', offer_soup.find('table', {'class': 'details'}).find('th', text=re.compile(r'Этажность')).next_sibling.string)
        except AttributeError:
            self._log.print_log('Ошибка при поиске тега в soup при парсинге этажа и этажности', self._log.ERROR)
        except:
            self._log.print_log('Неизвестная ошибка при парсинге года постройки дома', self._log.ERROR)
        return None

    def _get_offer_full_address (self, offer_soup: soup) -> str:
        """
        Парсит информацию об адресе квартиры. Адрес в формате удобном для работы с ФИАС, состоит из 4-ёх элементов.
        
        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Адрес квартиры в виде строки, состоящей из 4-ёх элементов:
                            Республика Коми, район, населенный пункт, улица и дом.
        """
        try:
            offer_info_tmp = offer_soup.find('div', {'class': 'main-heading container flex-row'}). \
                find('h1', {'class': 'main-heading__title'}).text.strip().split(', ')

            addr_region = 'Республика Коми'
            addr_raion = offer_soup.find('nav', {'aria-label':'breadcrumb'}).find_all('span', {'itemprop': 'name'})[1].text
            addr_city = 'Сыктывкар'
            if len(offer_info_tmp) == 3:
                addr_city = offer_info_tmp[2]
            offer_street_tmp: list = offer_info_tmp[1].split(' ')
            addr_street = ' '.join (offer_street_tmp[:-1])
            addr_house = offer_street_tmp[-1]
            # проверка и замена элементов в соответствии с правилами ФИАС для Сыктывкара
            syktyvkar_districts_fias = ['Верхний Мартыю', 'Выльтыдор', 'Трехозерка', 'Трехозёрка', 'Верхняя Максаковка', 'Краснозатонский', 'Седкыркещ']
            if (addr_raion == 'Сыктывкар') and (not addr_city in syktyvkar_districts_fias):
                addr_city = 'Сыктывкар'
            return f'{addr_region}, {addr_raion}, {addr_city}, {addr_street}, {addr_house}'
        except:
            self._log.print_log ('Неизвестная ошибка при получении адреса квартиры', self._log.ERROR)
            return None

    def _get_offer_phone_numbers (self, offer_soup_clicked: soup) -> str:
        """
        Парсит информацию о телефонных номерах. Может использоваться только для soup'а предложения, после нажатия на кнопку "Показать телефон".
        
        Аргументы:      offer_soup_clicked - soup предложения, полученный с вебдрайвером после нажатия на кнопку. 
        Возвращает:     Строку с телефоном(-телефонами), если их больше одного.
        """
        try:    
            phone_numbers_soup = offer_soup_clicked.find('div', {'class', 'contact'}).find_all('a', {'class': 'link phone ico _call'})
            phone_numbers_list = []
            for phone in phone_numbers_soup:
                phone_numbers_list.append(phone.text.replace(' ', ''))
            phone_numbers_str = ', '.join(phone_numbers_list).strip()
            return phone_numbers_str
        except:
            self._log.print_log ('Неизвестная ошибка при получении телефонных номеров', self._log.ERROR)
            return None

    def _get_offer_price (self, offer_soup: soup) -> int:
        """
        Парсит информацию о цене квартиры.
        
        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Строку с телефоном(-телефонами), если их больше одного.
        """
        try:
            return int(offer_soup.find('div', {'style': 'font-size:24px; color:#e52;'}).string.replace('руб.', '').replace('\xa0', '').replace(' ', '')) 
        except TypeError:
            self._log.print_log ('Ошибка при преобразовании типа данных при сборе цены квартиры', self._log.ERROR)
        except:
            return None

    def _get_offer_seller (self, offer_soup: soup) -> str:
        """
        Парсит данные о продавце квартиры.
        
        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Данные о продавце типа str.
        """
        try:
            offer_seller = offer_soup.find('div', {'class': 'ico _user-book'})
            if offer_seller:
                return offer_seller.find('a', {'class': 'link agency'}).text 
        except AttributeError:
            self._log.print_log('Данные о продавце квартиры не найдены', self._log.ERROR)
        except:
            self._log.print_log('Неизвестная ошибка получении информации о продавце', self._log.ERROR)
        return None

    def _get_offer_rooms_quantity (self, offer_soup: soup) -> int:
        """ 
        Парсит количество комнат в предложении.
        
        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Число комнат в квартире типа int. 
        """
        try:
            return int((re.findall(r'\d+', offer_soup.find('table', {'class': 'details'}).find('th', text=re.compile(r'Вид объекта')).next_sibling.string))[0])
        except AttributeError:
            self._log.print_log ('Не удалось найти количество комнат при парсинге характеристик', self._log.ERROR)
        except TypeError:
            self._log.print_log ('Ошибка преобразования типа данных при парсинге количества комнат', self._log.ERROR)
        except:
            self._log.print_log ('Неизвестная ошибка при получении количества комнат в предложении', self._log.ERROR)
        return None

    def _get_offer_total_area (self, offer_soup: soup) -> float:
        """
        Парсит всю информацию о площади квартиры. Из них выбирает только общую площадь.

        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Общая площадь квартиры типа float.
        """
        try:
            return float(
                str(offer_soup.find('table', {'class': 'details'}).find('th', text=re.compile(r'Площадь')).next_sibling.string)
                .replace('\xa0м²', '')
                .split(" / ")[0].replace(',', '.')
            )
        except AttributeError:
            return None
        except TypeError:
            self._log.print_log ('Ошибка при преобразовании типа данных при получении общей площади', self._log.ERROR)
        except:
            self._log.print_log ('Неизвестная ошибка при получении общей площади квартиры', self._log.ERROR)
        return None

    def _get_offer_walls_type (self, offer_soup: soup) -> str:
        """
        Парсит вид стен здания в предложении.
        
        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Вид стен здания типа str. 
        """
        try:
            return str(offer_soup.find('table', {'class': 'details'}).find('th', text=re.compile(r'Материал здания')).next_sibling.string)
        except AttributeError:
            return None
        except TypeError:
            self._log.print_log ('Нет возможности преобразовать материал стен в здании в тип str', self._log.ERROR)
        except:
            self._log.print_log ('Неизвестная ошибка при получении материала стен здания в предложении', self._log.ERROR)
        return None

    def _get_renovation_type (self, offer_soup: soup) -> str:
        """
        Парсит отделку помещения в предолжении.
        
        Аргументы:      offer_soup - soup предложения, полученный по URL. 
        Возвращает:     Отделку помещения в квартире типа str. 
        """
        try:
            return offer_soup.find('table', {'class': 'details'}).find('th', text=re.compile(r'Отделка')).next_sibling.string
        except AttributeError:
            return None
        except TypeError:
            self._log.print_log ('Нет возможности преобразовать строку в цену', self._log.ERROR)
        except:
            self._log.print_log ('Неизвестная ошибка при получении типа отделки квартиры', self._log.ERROR)
        return None

    def _get_page_offer_ids (self, page_soup: soup) -> list:
        """
        Собирает ID всех предожений, которые есть на странице.
        
        Аргументы:      page_soup - Beautifulsoup страницы. 
        Возвращает:     Список с ID предложений на странице. 
        """
        try:
            return [int(tag['id'].strip('ofer- '))
                for tag in page_soup.select('a[id]') if tag]
        except:
            self._log.print_log ('Критическая ошибка при сборе ID со страницы', self._log.CRITICAL)
        return []


    def _get_page_offer_prices (self, page_soup: soup) -> list:
        """
        Собирает цены всех предожений, которые есть на странице.
        
        Аргументы:      page_soup - Beautifulsoup страницы. 
        Возвращает:     Список со всеми ценами предложений на странице. 
        """
        prices_tmp = []
        for tag in page_soup.find_all('td', {'class': 'offer-table__cell _price'}):
            try:
                prices_tmp.append(int(tag.string.replace('\xa0', '')))
            except ValueError:
                tag = None
                prices_tmp.append(tag)
        return prices_tmp

    def _remove_offer_duplicates (self) -> None:
        """
        Обновляет переменную self._offer_ids, оставляя offer_id без повторов типа str. Удаляет из БД объявления с новой ценой.

        Аргументы: - 
        Возвращает: -
        """
        self._log.print_log('Удаляем дубликаты')
        cursor = self._db_connection.cursor()
        sql_query = (
            """
            SELECT offer_id, price, offer_stop_date
            FROM t_offers_tmp
            WHERE (offer_start_date > CURRENT_DATE - INTERVAL '1 year') AND (offer_url LIKE '%%167000%%')
            UNION ALL
            SELECT offer_id, price, offer_stop_date
            FROM t_offers
            WHERE (offer_start_date > CURRENT_DATE - INTERVAL '1 year') AND (offer_url LIKE '%%167000%%');
            """
        )
        cursor.execute(sql_query)
        db_result = cursor.fetchall() 
        db_data = {}
        for row in db_result:
            db_data[row[0]] = [row[1], row[2]]
        self._log.print_log ('Производим обновление даты закрытия объявления в базе данных.')
        self._stop_date_update(parsed_ids=self._parsed_ids_and_prices, db_data=db_data)
        delete_from_db = []
        parsed_ids = list(self._parsed_ids_and_prices.keys())
        for offer_id in parsed_ids:
            try:
                if db_data[offer_id][0] != self._parsed_ids_and_prices[offer_id]:
                    delete_from_db.append(offer_id)
                else:
                    del self._parsed_ids_and_prices[offer_id]
            except KeyError:
                pass
        delete_from_db = tuple(delete_from_db)
        if delete_from_db: 
            self._log.print_log ('Обнаружены объявления, внесенные в базу данных, с изменившейся ценой на сайте.')
            self._log.print_log ('Удаляем из базы данных объявления с изменившейся ценой.')
            try:    
                cursor.execute("DELETE FROM t_offers_tmp WHERE (offer_id IN %s) AND (offer_url LIKE '%%167000%%')", (delete_from_db,))
                cursor.execute("DELETE FROM t_offers WHERE (offer_id IN %s) AND (offer_url LIKE '%%167000%%')", (delete_from_db,))
            except:
                self._log.print_log ('Ошибка при удалении объявлений из базы.', self._log.ERROR)
            self._db_connection.commit()
        cursor.close()
        self._offer_ids = [str(offer_id) for offer_id in self._parsed_ids_and_prices.keys()]

    def _stop_date_update (self, parsed_ids: dict, db_data: dict) -> None:
            """
            Обновляет в БД столбец по дате закрытия объявления. 
            Для этого обрабатывает словарь со спарсенными объявлениями и объявлениями из базы данных. 
            
            Аргументы:      parsed_ids - словарь спарсенных обявлений со значением цены.
                            db_data - словарь объявлений из БД со значениями цены и даты закрытия объявления. 
            Возвращает:     -
            """
            cursor = self._db_connection.cursor()
            update_stop_date_db = []
            for key in parsed_ids.keys():
                if db_data.get(key) != None:
                    update_stop_date_db.append(key)
            update_stop_date_db = tuple(update_stop_date_db)
            if update_stop_date_db:
                cursor.execute("UPDATE t_offers_tmp SET offer_stop_date = NULL WHERE (offer_id IN %s) AND (offer_url LIKE '%%167000%%')", (update_stop_date_db,)) 
                cursor.execute("UPDATE t_offers SET offer_stop_date = NULL WHERE (offer_id IN %s) AND (offer_url LIKE '%%167000%%')", (update_stop_date_db,))
            stop_date_yesterday = []
            for key, value in list(db_data.items()):
                if (parsed_ids.get(key) == None) and (value[1] == None):
                    stop_date_yesterday.append(key)
            stop_date_yesterday = tuple(stop_date_yesterday)
            if stop_date_yesterday:
                cursor.execute("UPDATE t_offers_tmp SET offer_stop_date = current_date - 1 WHERE (offer_id IN %s) AND (offer_url LIKE '%%167000%%')", (stop_date_yesterday,))
                cursor.execute("UPDATE t_offers SET offer_stop_date = current_date - 1 WHERE (offer_id IN %s) AND (offer_url LIKE '%%167000%%')", (stop_date_yesterday,))
            self._db_connection.commit()
            cursor.close()
    
    def _get_offer_characteristics(self, offer_id: str) -> tuple: 
        """
        Реализует нажатие на кнопку на странице с предложением, парсит все характеристики объекта со страницы, подготавливает данные к импорту в БД.
        
        Аргументы:          offer_id  Уникальный номер предложения в формате строки
        Возвращает:         кортеж с характеристиками предложения с подготовленными данными для внесения в БД.
        """
        try:
            # подключение к странице с предложением
            offer_url = f'http://167000.ru/o/{offer_id}/'
            self._log.print_log(f'Парсинг объявления: {offer_url}')
            self._chrome_driver.get(offer_url)
            # нажатие на кнопку 
            time.sleep(2)
            try:    
                self._chrome_driver.find_element(By.TAG_NAME, 'button').click()
            except:
                self._log.print_log('Ошибка при реализации нажатия на кнопку в браузере', self._log.ERROR)
            time.sleep(10)
            # получаем соуп страницы после нажатия на кнопку
            page_soup = soup(self._chrome_driver.page_source, features='lxml')
            # сбор характеристик объекта
            db_values = []
            db_values.append(uuid.uuid4())
            db_values.append(offer_id)
            db_values.append(f'http://167000.ru/o/{offer_id}/')
            db_values.append(self._capture_screenshot(offer_id))
            db_values.append(self._get_offer_date(page_soup))
            db_values.append(None) 
            db_values.append(self._get_offer_full_address(page_soup))
            db_values.append(self._get_offer_price(page_soup))
            db_values.append(self._get_offer_rooms_quantity(page_soup))
            db_values.append(self._get_offer_total_area(page_soup))
            try:
                db_values.append(int(self._get_offer_floors_info(page_soup)[0]))
            except:
                db_values.append(None)
            try:
                db_values.append(int(self._get_offer_floors_info(page_soup)[1]))
            except:
                db_values.append(None)
            db_values.append(self._get_offer_walls_type(page_soup))
            db_values.append(self._get_renovation_type(page_soup))
            db_values.append(self._get_offer_construction_year(page_soup))
            db_values.append(self._get_offer_description(page_soup))
            db_values.append(self._get_offer_seller(page_soup))
            db_values.append(self._get_offer_phone_numbers(page_soup))
            # подготовка данных в бд
            psycopg2.extras.register_uuid()
            return tuple ([adapt(value) if not value is None else None for value in db_values])
        except:
            self._log.print_log(f'Неизвестная ошибка при парсинге объявления: {offer_url}', self._log.ERROR)
            pass

    def _capture_screenshot(self, file_name: str) -> str:
            """
            Сохраняет скриншоты страниц, адреса которых передаются в списке. 
                
            Возвращает путь скриншота в виде строки. 
            Аргументы
                file_name       название файла для скриншота, уникальный номер объявления
            """
            if isinstance(file_name, str) and file_name != '':
                file_name = '167000_' + file_name
            try:    
                page_rect = self._chrome_driver.execute_cdp_cmd('Page.getLayoutMetrics', {})
                screenshot_config = {
                    'captureBeyondViewport': True,
                    'fromSurface': True,
                    'clip':
                        {'width': page_rect['contentSize']['width'],
                        'height': page_rect['contentSize']['height'],
                        'x': 0,
                        'y': 0,
                        'scale': 1},
                }
                img = Image.open(BytesIO(base64.b64decode(self._chrome_driver.execute_cdp_cmd(
                    'Page.captureScreenshot', screenshot_config)['data'])))
                width = screenshot_config['clip']['width']
                height = screenshot_config['clip']['height']
                if self._SCRSHOT_WIDTH != 0 and width > self._SCRSHOT_WIDTH:
                    crop_horizontal = (width - self._SCRSHOT_WIDTH) // 2
                else:
                    crop_horizontal = 0
                if self._SCRSHOT_HEIGHT != 0 and height > self._CRSHOT_HEIGHT:
                    crop_vertical = (height - self._SCRSHOT_WIDTH) // 2
                else:
                    crop_vertical = 0
                img = img.crop((
                    crop_horizontal,
                    crop_vertical,
                    width - crop_horizontal,
                    height - crop_vertical))
                if self._SCRSHOT_USE_JPG:
                    img.convert('RGB').save(self._SCRSHOT_PATH + file_name +
                                            '.jpg', quality=self._SCRSHOT_QUAL)
                else:
                    img.save(self._SCRSHOT_PATH + file_name + '.png')
                img.close
                    
                image_path = str(self._SCRSHOT_PATH  + file_name)
                return image_path
            except:
                self._log.print_log('Неизвестная ошибка при сохранении скриншота', self._log.ERROR)
            return None
        
    @property
    def offer_ids(self) -> list:
        """
        Список с offer_id для парсинга характеристик.
        """
        return self._offer_ids

    @property
    def all_offers_characteristics(self) -> list:
        """
        Список кортежей с характеристиками спарсенных объектов. Характеристики обработаны adapt для внесения в БД.
        """
        return self._all_offers_characteristics
