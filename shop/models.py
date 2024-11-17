from django.db import models
from django.utils.text import slugify
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator

class Category(models.Model):
    name=models.CharField(max_length=200)
    slug=models.SlugField(max_length=200,unique=True)

    class Meta:
        ordering=['name']
        indexes=[
            models.Index(fields=['name']),
        ]
        verbose_name='category'
        verbose_name_plural='categories'

    def save(self,*args, **kwargs):
        if not self.slug:
            self.slug=slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Product(models.Model):
    id=models.UUIDField(primary_key=True,editable=False,default=uuid.uuid4,unique=True)
    category=models.ForeignKey(Category,on_delete=models.CASCADE,related_name='category_products')
    name=models.CharField(max_length=200)
    slug=models.SlugField(max_length=200)
    description=models.TextField(blank=True)
    price=models.DecimalField(max_digits=10,decimal_places=2)
    available=models.BooleanField(default=True)
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)

    class Meta:
        ordering=['name']
        indexes=[
            models.Index(fields=['id','slug']),
            models.Index(fields=['name']),
            models.Index(fields=['-created'])
        ]

    def save(self,*args, **kwargs):
        if not self.slug:
            self.slug=slugify(self.name)
        super().save(*args, **kwargs)


    def __str__(self):
        return self.name



class Image(models.Model):

    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='product_images')
    image=models.ImageField(upload_to='products_image')

    def __str__(self):
        return f'prodcut_{self.product.id}:{self.image}'






class Order(models.Model):
    coupon = models.ForeignKey('Coupon',related_name='orders',null=True,blank=True,on_delete=models.SET_NULL)
    first_name=models.CharField(max_length=50)
    last_name=models.CharField(max_length=50)
    email=models.EmailField()
    address=models.CharField(max_length=250)
    postal_code=models.CharField(max_length=20)
    city=models.CharField(max_length=50)
    created=models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(auto_now=True)
    paid=models.BooleanField(default=False)
    discount = models.IntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(100)])


    class Meta:
        ordering=['-created']
        indexes=[
        models.Index(fields=('-created',))
        ]

    def __str__(self):
        return f'order:{self.id}'

    def get_total_cost(self):
        total_cost = self.get_total_cost_before_discount()
        return total_cost - self.get_discount()


    def get_total_cost_before_discount(self):
        return sum(item.get_cost() for item in self.items.all())


    def get_discount(self):
        total_cost = self.get_total_cost_before_discount()
        if self.discount:
            return total_cost * (self.discount / Decimal(100))
        return Decimal(0)





class OrderItem(models.Model):
    order=models.ForeignKey(Order,on_delete=models.CASCADE,related_name='items')
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='order_items')
    price=models.DecimalField(max_digits=10,decimal_places=2)
    quantity=models.PositiveIntegerField(default=1)


    def __str__(self):
        return str(self.id)
    
    def get_cost(self):
        return self.price * self.quantity




class Coupon(models.Model):
    code=models.CharField(max_length=50,unique=True)
    valid_from=models.DateTimeField()
    valid_to=models.DateTimeField()
    discount=models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(100)],help_text='Percentage value (0 to 100)')
    active=models.BooleanField()
    def __str__(self):
        return self.code