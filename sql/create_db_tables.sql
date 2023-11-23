-- public.d_building_types definition

-- Drop table

-- DROP TABLE public.d_building_types;

CREATE TABLE public.d_building_types (
	building_type_id int4 NOT NULL, -- Идентификатор
	building_rr_code varchar(12) NULL, -- Код типа здания в Росреестре
	building_type_name varchar NULL, -- Наименование типа здания
	CONSTRAINT d_building_types_pkey PRIMARY KEY (building_type_id)
);
CREATE INDEX d_building_types_building_rr_code_idx ON public.d_building_types USING btree (building_rr_code);
COMMENT ON TABLE public.d_building_types IS 'Назначение зданий по Ростреестру';

-- Column comments

COMMENT ON COLUMN public.d_building_types.building_type_id IS 'Идентификатор';
COMMENT ON COLUMN public.d_building_types.building_rr_code IS 'Код типа здания в Росреестре';
COMMENT ON COLUMN public.d_building_types.building_type_name IS 'Наименование типа здания';


-- public.d_flat_types definition

-- Drop table

-- DROP TABLE public.d_flat_types;

CREATE TABLE public.d_flat_types (
	flat_type_id int4 NOT NULL, -- Идентификатор
	flat_rr_code varchar(12) NULL, -- Код помещения в Росреестре
	flat_type_name varchar NULL, -- Наименование типа помещения
	CONSTRAINT d_flat_types_pkey PRIMARY KEY (flat_type_id)
);
CREATE INDEX d_flat_types_flat_rr_code_idx ON public.d_flat_types USING btree (flat_rr_code);
COMMENT ON TABLE public.d_flat_types IS 'Назначение помещений по Росреестру';

-- Column comments

COMMENT ON COLUMN public.d_flat_types.flat_type_id IS 'Идентификатор';
COMMENT ON COLUMN public.d_flat_types.flat_rr_code IS 'Код помещения в Росреестре';
COMMENT ON COLUMN public.d_flat_types.flat_type_name IS 'Наименование типа помещения';


-- public.d_group definition

-- Drop table

-- DROP TABLE public.d_group;

CREATE TABLE public.d_group (
	group_id int4 NOT NULL, -- Идентификатор группы
	group_name varchar NULL, -- Наименование группы
	CONSTRAINT d_group_pkey PRIMARY KEY (group_id)
);
COMMENT ON TABLE public.d_group IS 'Словарь групп';

-- Column comments

COMMENT ON COLUMN public.d_group.group_id IS 'Идентификатор группы';
COMMENT ON COLUMN public.d_group.group_name IS 'Наименование группы';


-- public.d_offer_types definition

-- Drop table

-- DROP TABLE public.d_offer_types;

CREATE TABLE public.d_offer_types (
	offer_type_id int4 NOT NULL, -- Идентификатор
	offer_type_name varchar NULL, -- Тип объявления. Например: Продажа, аренда
	CONSTRAINT d_offer_types_pkey PRIMARY KEY (offer_type_id)
);
COMMENT ON TABLE public.d_offer_types IS 'Типы объявлений';

-- Column comments

COMMENT ON COLUMN public.d_offer_types.offer_type_id IS 'Идентификатор';
COMMENT ON COLUMN public.d_offer_types.offer_type_name IS 'Тип объявления. Например: Продажа, аренда';


-- public.d_renovation_types definition

-- Drop table

-- DROP TABLE public.d_renovation_types;

CREATE TABLE public.d_renovation_types (
	renovation_type_id int4 NOT NULL, -- Идентификатор
	renovation_type_name varchar NULL, -- Отделка помещения - тип ремонта
	CONSTRAINT d_renovation_types_pkey PRIMARY KEY (renovation_type_id)
);
COMMENT ON TABLE public.d_renovation_types IS 'Типы ремонтов';

-- Column comments

COMMENT ON COLUMN public.d_renovation_types.renovation_type_id IS 'Идентификатор';
COMMENT ON COLUMN public.d_renovation_types.renovation_type_name IS 'Отделка помещения - тип ремонта';


-- public.d_sale_types definition

-- Drop table

-- DROP TABLE public.d_sale_types;

CREATE TABLE public.d_sale_types (
	sale_type_id int4 NOT NULL, -- Идентификатор
	sale_type_name varchar NULL, -- Тип продажи. Например: первичная от юр.лица
	CONSTRAINT d_sale_types_pkey PRIMARY KEY (sale_type_id)
);
COMMENT ON TABLE public.d_sale_types IS 'Типы продаж';

-- Column comments

COMMENT ON COLUMN public.d_sale_types.sale_type_id IS 'Идентификатор';
COMMENT ON COLUMN public.d_sale_types.sale_type_name IS 'Тип продажи. Например: первичная от юр.лица';


-- public.d_walls definition

-- Drop table

-- DROP TABLE public.d_walls;

CREATE TABLE public.d_walls (
	walls_type_id int4 NOT NULL, -- Идентификатор типа стен здания
	walls_type_rr_code varchar(12) NULL, -- Код типа стен здания в Росреестре
	walls_type_name varchar NULL, -- Наименование материала стен
	CONSTRAINT d_walls_pkey PRIMARY KEY (walls_type_id)
);
CREATE INDEX d_walls_walls_type_rr_code_idx ON public.d_walls USING btree (walls_type_rr_code);
COMMENT ON TABLE public.d_walls IS 'Материалы стен по Росреестру';

-- Column comments

COMMENT ON COLUMN public.d_walls.walls_type_id IS 'Идентификатор типа стен здания';
COMMENT ON COLUMN public.d_walls.walls_type_rr_code IS 'Код типа стен здания в Росреестре';
COMMENT ON COLUMN public.d_walls.walls_type_name IS 'Наименование материала стен';


-- public.t_offers_tmp definition

-- Drop table

-- DROP TABLE public.t_offers_tmp;

CREATE TABLE public.t_offers_tmp (
	offer_tmp_id uuid NOT NULL, -- Идентификатор во временной таблице объявлений
	offer_id int8 NOT NULL, -- Идентификатор объявления на площадке
	offer_url varchar NULL, -- URL-ссылка на объявление
	offer_screenshot_path varchar NULL, -- Путь на диск скриншота объявления
	offer_start_date date NULL, -- Дата первой публикации объявления
	offer_stop_date date NULL, -- Дата снятия обявления
	address text NULL, -- Адрес
	price int4 NULL, -- Цена
	rooms_total int4 NULL, -- Количество комнат
	total_area float8 NULL, -- Общая площадь
	flat_floor int4 NULL, -- Этаж помещения
	total_floors int4 NULL, -- Общая этажность здания
	walls_type varchar NULL, -- Материал стен
	renovation_type varchar NULL, -- Отделка - тип ремонта
	construction_year int4 NULL, -- Год постройки
	offer_description varchar NULL, -- Описание объявления
	offer_seller varchar NULL, -- Продавец (Пример: частное лицо, риелтор)
	phone_numbers varchar NULL, -- Номер телефона (Сбор только в 167000.ru)
	CONSTRAINT t_offers_tmp_pkey PRIMARY KEY (offer_tmp_id)
);
COMMENT ON TABLE public.t_offers_tmp IS 'Временная таблица с предложениями для обработки вручную';

-- Column comments

COMMENT ON COLUMN public.t_offers_tmp.offer_tmp_id IS 'Идентификатор во временной таблице объявлений';
COMMENT ON COLUMN public.t_offers_tmp.offer_id IS 'Идентификатор объявления на площадке';
COMMENT ON COLUMN public.t_offers_tmp.offer_url IS 'URL-ссылка на объявление';
COMMENT ON COLUMN public.t_offers_tmp.offer_screenshot_path IS 'Путь на диск скриншота объявления';
COMMENT ON COLUMN public.t_offers_tmp.offer_start_date IS 'Дата первой публикации объявления';
COMMENT ON COLUMN public.t_offers_tmp.offer_stop_date IS 'Дата снятия обявления';
COMMENT ON COLUMN public.t_offers_tmp.address IS 'Адрес';
COMMENT ON COLUMN public.t_offers_tmp.price IS 'Цена';
COMMENT ON COLUMN public.t_offers_tmp.rooms_total IS 'Количество комнат';
COMMENT ON COLUMN public.t_offers_tmp.total_area IS 'Общая площадь';
COMMENT ON COLUMN public.t_offers_tmp.flat_floor IS 'Этаж помещения';
COMMENT ON COLUMN public.t_offers_tmp.total_floors IS 'Общая этажность здания';
COMMENT ON COLUMN public.t_offers_tmp.walls_type IS 'Материал стен';
COMMENT ON COLUMN public.t_offers_tmp.renovation_type IS 'Отделка - тип ремонта';
COMMENT ON COLUMN public.t_offers_tmp.construction_year IS 'Год постройки';
COMMENT ON COLUMN public.t_offers_tmp.offer_description IS 'Описание объявления';
COMMENT ON COLUMN public.t_offers_tmp.offer_seller IS 'Продавец (Пример: частное лицо, риелтор)';
COMMENT ON COLUMN public.t_offers_tmp.phone_numbers IS 'Номер телефона (Сбор только в 167000.ru)';


-- public.d_subgroup definition

-- Drop table

-- DROP TABLE public.d_subgroup;

CREATE TABLE public.d_subgroup (
	subgroup_id int4 NOT NULL, -- Идентификатор подгруппы
	group_id int4 NOT NULL, -- Идентификатор группы
	subgroup_name varchar NULL, -- Наименование подгруппы
	CONSTRAINT d_subgroup_pkey PRIMARY KEY (subgroup_id),
	CONSTRAINT d_subgroup_group_id_fk FOREIGN KEY (group_id) REFERENCES public.d_group(group_id) ON DELETE CASCADE
);
CREATE INDEX d_subgroup_group_id_idx ON public.d_subgroup USING btree (group_id);
COMMENT ON TABLE public.d_subgroup IS 'Словарь подгрупп';

-- Column comments

COMMENT ON COLUMN public.d_subgroup.subgroup_id IS 'Идентификатор подгруппы';
COMMENT ON COLUMN public.d_subgroup.group_id IS 'Идентификатор группы';
COMMENT ON COLUMN public.d_subgroup.subgroup_name IS 'Наименование подгруппы';


-- public.t_offers definition

-- Drop table

-- DROP TABLE public.t_offers;

CREATE TABLE public.t_offers (
	offer_id int4 NOT NULL, -- Идентификатор объявления на площадке
	offer_url varchar NULL, -- URL-ссылка на объявление
	offer_screenshot_path varchar NULL, -- Путь на диск скриншота объявления
	offer_start_date date NULL, -- Дата первой публикации объявления
	offer_stop_date date NULL, -- Дата снятия обявления
	address text NULL, -- Адрес
	price int4 NULL, -- Цена
	rooms_total int4 NULL, -- Количество комнат
	total_area float8 NULL, -- Общая площадь
	flat_floor int4 NULL, -- Этаж помещения
	total_floors int4 NULL, -- Общая этажность здания
	walls_type varchar NULL, -- Материал стен
	renovation_type varchar NULL, -- Отделка - тип ремонта
	construction_year int4 NULL, -- Год постройки
	offer_description varchar NULL, -- Описание объявления
	offer_seller varchar NULL, -- Продавец (Пример: частное лицо, риелтор)
	phone_number varchar NULL, -- Номер телефона (Сбор только в 167000.ru)
	offer_type_id int4 NULL, -- Тип объявления
	sale_type_id int4 NULL, -- Тип продажи
	is_rejected bool NULL, -- Выброс или нет
	"comment" text NULL, -- Комментарий к объявлению
	notebook text NULL, -- Примечание к объявлению
	CONSTRAINT t_offers_pkey PRIMARY KEY (offer_id),
	CONSTRAINT t_offers_offer_type_id_fk FOREIGN KEY (offer_type_id) REFERENCES public.d_offer_types(offer_type_id) ON DELETE CASCADE,
	CONSTRAINT t_offers_sale_type_id_fk FOREIGN KEY (sale_type_id) REFERENCES public.d_sale_types(sale_type_id) ON DELETE CASCADE
);
COMMENT ON TABLE public.t_offers IS 'Список объявлений по продаже квартир';

-- Column comments

COMMENT ON COLUMN public.t_offers.offer_id IS 'Идентификатор объявления на площадке';
COMMENT ON COLUMN public.t_offers.offer_url IS 'URL-ссылка на объявление';
COMMENT ON COLUMN public.t_offers.offer_screenshot_path IS 'Путь на диск скриншота объявления';
COMMENT ON COLUMN public.t_offers.offer_start_date IS 'Дата первой публикации объявления';
COMMENT ON COLUMN public.t_offers.offer_stop_date IS 'Дата снятия обявления';
COMMENT ON COLUMN public.t_offers.address IS 'Адрес';
COMMENT ON COLUMN public.t_offers.price IS 'Цена';
COMMENT ON COLUMN public.t_offers.rooms_total IS 'Количество комнат';
COMMENT ON COLUMN public.t_offers.total_area IS 'Общая площадь';
COMMENT ON COLUMN public.t_offers.flat_floor IS 'Этаж помещения';
COMMENT ON COLUMN public.t_offers.total_floors IS 'Общая этажность здания';
COMMENT ON COLUMN public.t_offers.walls_type IS 'Материал стен';
COMMENT ON COLUMN public.t_offers.renovation_type IS 'Отделка - тип ремонта';
COMMENT ON COLUMN public.t_offers.construction_year IS 'Год постройки';
COMMENT ON COLUMN public.t_offers.offer_description IS 'Описание объявления';
COMMENT ON COLUMN public.t_offers.offer_seller IS 'Продавец (Пример: частное лицо, риелтор)';
COMMENT ON COLUMN public.t_offers.phone_number IS 'Номер телефона (Сбор только в 167000.ru)';
COMMENT ON COLUMN public.t_offers.offer_type_id IS 'Тип объявления';
COMMENT ON COLUMN public.t_offers.sale_type_id IS 'Тип продажи';
COMMENT ON COLUMN public.t_offers.is_rejected IS 'Выброс или нет';
COMMENT ON COLUMN public.t_offers."comment" IS 'Комментарий к объявлению';
COMMENT ON COLUMN public.t_offers.notebook IS 'Примечание к объявлению';