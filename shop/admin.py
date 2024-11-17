from django.contrib import admin
from .models import *
# Register your models here.
from django.http import HttpResponse
import csv
import datetime

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display=['id','name','slug','description','available','price','created','updated']
    prepopulated_fields={'slug':('name',)}
    list_filter=['available','created','updated']
    list_editable=['price','available']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display=['name','slug']
    prepopulated_fields={'slug':('name',)}


@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display=['product','image']


class OrderItemInline(admin.TabularInline):
    model=OrderItem



def export_to_csv(modeladmin,request,queryset):
    opts = modeladmin.model._meta
    content_disposition = f'attachment; filename={opts.verbose_name}.csv'
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = content_disposition
    writer=csv.writer(response)
    fields=[field for field in opts.get_fields() if not \
        field.many_to_many and not field.one_to_many
        ]

    # Write a first row with header information 
    writer.writerow([field.verbose_name for field in fields])

    for obj in queryset:
        data_row=[]
        for field in fields:
            value=getattr(obj,field.name)
            if isinstance(value,datetime.datetime):
                value=value.strftime('%d/%m/%Y')
            data_row.append(value)
        writer.writerow(data_row)
    return response
export_to_csv.short_description = 'Export to CSV' 




@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display=['first_name','last_name','email','address','postal_code','city','created','updated','paid']
    list_filter=['paid','created']
    inlines=[OrderItemInline]
    actions = [export_to_csv]



@admin.register(Coupon)
class CoubonAdmin(admin.ModelAdmin):
    list_display=['code','valid_from','valid_to','discount','active']
    list_filter = ['active', 'valid_from', 'valid_to']
    search_fields = ['code']