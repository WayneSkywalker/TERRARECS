from django.contrib import admin

from .models import Page, Transaction, Place, District, Amphur, Province, Setting

admin.site.site_header = 'TERRARECS ADMIN'
admin.site.site_title = 'TERRARECS ADMIN'
admin.site.index_title = 'TERRARECS Administration site'

admin.site.register(Page)
admin.site.register(Transaction)
admin.site.register(Place)
admin.site.register(District)
admin.site.register(Amphur)
admin.site.register(Province)
admin.site.register(Setting)