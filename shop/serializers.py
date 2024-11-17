from rest_framework import serializers
from .models import *
from django.shortcuts import get_object_or_404


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model=Category
        fields=['name','slug']

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model=Image
        fields=['image']

class ProductSerializer(serializers.ModelSerializer):
    category=serializers.StringRelatedField()
    product_images=ImageSerializer(many=True,read_only=True)
    uploaded_images=serializers.ListField(write_only=True,child=serializers.ImageField(max_length=1000000,allow_empty_file=False,use_url=False))

    class Meta:
        model=Product
        fields=['name','slug','description','price','created','updated','category','product_images','uploaded_images']
        read_only_fields=['created','updated']


    def create(self,validated_data):
        images=validated_data.pop('uploaded_images')
        category,created=Category.objects.get_or_create(name=self.context['data']['category'])
        product=Product.objects.create(category=category,**validated_data)
        for p_image in images:
            Image.objects.create(product=product,image=p_image)
        return product



class ProductUpdateSerializer(ProductSerializer):

    def to_representation(self,instance):
        data=super().to_representation(instance)
        data['in_cart']=self.context['cart'].in_cart(str(instance.id))
        return data


class ProductCartSerializer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields=['id','name','price']



class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model=Order
        fields=['first_name','last_name','email','city','address','postal_code']




class CouponSerializer(serializers.Serializer):
    code=serializers.CharField(max_length=50)
