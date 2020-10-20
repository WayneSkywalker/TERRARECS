from django.db import models

class Province(models.Model):
    province_id = models.PositiveSmallIntegerField(primary_key = True, unique = True)
    th = models.CharField(max_length = 30, unique = True)
    en = models.CharField(max_length = 30, blank = True)

    class Meta:
        db_table = 'province'

    def __str__(self):
        return self.th

class Amphur(models.Model):
    amphur_id = models.PositiveSmallIntegerField(primary_key = True, unique = True)
    th = models.CharField(max_length = 30)
    en = models.CharField(max_length = 30, blank = True)

    province = models.ForeignKey(Province, related_name = 'province', on_delete = models.CASCADE)

    class Meta:
        db_table = 'amphur'

    def __str__(self):
        return self.th

class District(models.Model):
    district_id = models.PositiveSmallIntegerField(primary_key = True, unique = True)
    th = models.CharField(max_length = 30)
    en = models.CharField(max_length = 30, blank = True)

    amphur = models.ForeignKey(Amphur, related_name = 'amphur', on_delete = models.CASCADE)

    class Meta:
        db_table = 'district'
    
    def __str__(self):
        return self.th

class Page(models.Model):
    page_id = models.IntegerField(primary_key = True, unique = True)
    title_th = models.CharField(max_length = 3000)
    title_en = models.CharField(max_length = 3000, blank = True)
    lat = models.FloatField()
    lng = models.FloatField()
    # status = models.PositiveIntegerField()

    AREA_ID_CHOICES = (
        (1,'สีลม - สาทร'),
        (2,'สุขุมวิท - ชิดลม - ทองหล่อ - เอกมัย'),
        (3,'พญาไท - อารีย์ - สะพานควาย'),
        (4,'ตากสิน - วงเวียนใหญ่ - ธนบุรี'),
        (5,'รัชดา - ห้วยขวาง - ดินแดง'),
        (6,'พัฒนาการ - คลองตัน - ประเวศ'),
        (7,'อ่อนนุช - ศรีนครินทร์ - บางนา'),
        (8,'จตุจักร - ประชาชื่น - รัตนาธิเบศร์'),
        (9,'แจ้งวัฒนะ - ติวานนท์ - ดอนเมือง'),
        (10,'ลาดพร้าว - รามคำแหง - บางกะปิ'),
        (11,'เกษตรนวมินทร์ - รามอินทร'),
        (12,'วัชรพล - สายไหม'),
        (13,'สะพานสูง - มีนบุรี'),
        (14,'รังสิต - ลำลูกกา'),
        (15,'นนทบุรี - บางใหญ่ - บางบัวทอง'),
        (16,'ราชพฤกษ์ - นครอินทร์'),
        (17,'ปิ่นเกล้า - ตลิ่งชัน - พระราม 7'),
        (18,'เพชรเกษม - บางแค - พุทธมณฑล'),
        (19,'กัลปพฤกษ์ - เอกชัย'),
        (20,'สุขสวัสดิ์ - ทุ่งครุ - ราชฎร์บูรณะ'),
        (21,'พระราม 2 - บางขุนเทียน'),
        (22,'สมุทรปราการ'),
        (23,'ปทุมธานี'),
        (24,'อื่นๆ'),
        (25,'พระราม 3 - ยานนาวา'),
    )
    area_id = models.PositiveSmallIntegerField(choices = AREA_ID_CHOICES)

    rent_price = models.FloatField()
    sale_price = models.FloatField()

    POST_TYPE_CHOICES = (
        (1,'ขาย'),
        (2,'ขายดาวน์'),
        (3,'ขายและเช่า'),
        (4,'เช่า'),
        (5,'แนะนำโครงกรใหม่'),
    )
    post_type = models.PositiveSmallIntegerField(choices = POST_TYPE_CHOICES)

    HOUSE_TYPE_CHOICES = (
        (6,'บ้านเดี่ยว'),
        (7,'คอนโดมิเนียม'),
        (8,'ที่ดิน'),
        (9,'ทาวน์เฮ้าส์'),
        (10,'อาคารพาณิชย์'),
        (197,'บ้านแฝด'),
        (198,'โฮมออฟฟิศ'),
        (206,'โรงงาน'),
        (207,'โกดัง'),
        (208,'สำนักงาน'),
        (209,'อพาร์ทเม้นท์'),
        (210,'โรงแรม/โฮสเทล'),
        (11,'อื่นๆ'),
    )
    house_type = models.PositiveSmallIntegerField(choices = HOUSE_TYPE_CHOICES)

    landarea_total_sqw = models.FloatField()
    area_size_sqm = models.FloatField()
    
    distances_supermarket = models.FloatField()
    distances_department_store = models.FloatField()
    distances_education = models.FloatField()
    distances_transit = models.FloatField()

    district = models.ForeignKey(District, related_name = 'address_district', on_delete = models.CASCADE)
    amphur = models.ForeignKey(Amphur, related_name = 'address_amphur', on_delete = models.CASCADE)
    province = models.ForeignKey(Province, related_name = 'address_province', on_delete = models.CASCADE)

    # district_id
    # amphur_id
    # province_id

    ROOM_TYPE_CHOICES = (
        (0,'ไม่มีห้องนอน'),
        (41,'Penthouse'),
        (42,'Duplex'),
        (43,'Studio'),
        (44,'1 ห้องนอน'),
        (45,'2 ห้องนอน'),
        (46,'3 ห้องนอน'),
        (47,'4 ห้องนอน'),
        (48,'5 ห้องนอนขึ้นไป'),
    )
    room_type = models.PositiveSmallIntegerField(choices = ROOM_TYPE_CHOICES)

    class Meta:
        db_table = 'page'

    def __str__(self):
        return self.page_id

class Place(models.Model):
    name_th = models.CharField(max_length = 350)
    latitude = models.FloatField()
    longitude = models.FloatField()
    poi_type = models.CharField(max_length = 300) # ['Supermarket/ Convenience Store', 'school, university, education places', 'Department Store']

    district = models.ForeignKey(District, related_name = 'place_address_district', on_delete = models.CASCADE)
    amphur = models.ForeignKey(Amphur, related_name = 'place_address_amphur', on_delete = models.CASCADE)
    province = models.ForeignKey(Province, related_name = 'place_address_province', on_delete = models.CASCADE)

    class Meta:
        db_table = 'place'
    
    def __str__(self):
        return self.name_th

class Transit(models.Model):
    name_th = models.CharField(max_length = 100)
    name_en = models.CharField(max_length = 100, blank = True)
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        db_table = 'transit'
    
    def __str__(self):
        return self.name_th

class Transaction(models.Model):
    userID = models.CharField(max_length = 200)
    page = models.ForeignKey(Page, related_name = 'view_page', on_delete = models.CASCADE)
    event_strength = models.FloatField()

    class Meta:
        db_table = 'transaction'

    def __str__(self):
        return '%s viewed %d --> event_strength %f' % (self.userID, self.page.page_id, self.event_strength)

class Setting(models.Model):
    setting_name = models.CharField(max_length = 30, unique = True)
    
    RECS_TYPE_CHOICES = (
        (1,'NORMAL RECOMMENDER'),
        (2,'RECOMMENDER WITH TOP 3 CONTENT - BASED'),
        (3,'RECOMMENDER WITHOUT WEIGHTS'),
    )
    recs_type = models.PositiveSmallIntegerField(choices = RECS_TYPE_CHOICES, default = 1)

    cb_ensemble_weight = models.PositiveIntegerField(default = 1)
    cf_ensemble_weight = models.PositiveIntegerField(default = 1)
    k = models.PositiveSmallIntegerField(null = True, blank = True)
    topn = models.PositiveSmallIntegerField(null = True, blank = True)
    n_cb = models.PositiveSmallIntegerField(null = True, blank = True)
    n_cf = models.PositiveSmallIntegerField(null = True, blank = True)

    class Meta:
        db_table = 'setting'
        unique_together = [['recs_type','cb_ensemble_weight','cf_ensemble_weight','k','topn','n_cb','n_cf']]

    def __str__(self):
        return self.setting_name