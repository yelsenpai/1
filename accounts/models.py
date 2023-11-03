from django.db import models
from django.contrib.auth.models import  User

# class User(AbstractUser):
#     is_admin = models.BooleanField(default= False)
#     is_regularuser = models.BooleanField(default= False)




class Item(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    quantity = models.IntegerField()
    unit = models.CharField(max_length=255)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=2)
    department = models.CharField(max_length=255)
    purpose = models.TextField()
    
    # Add a user_id field to store the user's identifier for the request
    user_id = models.CharField(max_length=10, unique=True, blank=True, null=True)  # Adjust the max_length as needed

    # ... other fields ...

    def save(self, *args, **kwargs):
        # Generate a unique user_id for the request
        if not self.user_id:
            self.user_id = self.generate_unique_user_id()
        super().save(*args, **kwargs)

    def generate_unique_user_id(self):
        # Implement your logic to generate a unique user_id here
        # Example: Generate a random alphanumeric user_id
        # Make sure it's unique in your system
        import random
        import string

        while True:
            user_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            if not Item.objects.filter(user_id=user_id).exists():
                return user_id

    # ... other methods ...

    def __str__(self):
        return self.name






class VerificationCode(models.Model):
    email = models.EmailField()
    code = models.CharField(max_length=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Code: {self.code} for {self.email}'

class History(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purchase_request_id = models.CharField(max_length=20)
    date_requested = models.DateField()
    purpose = models.CharField(max_length=200)
    quantity = models.IntegerField()
    status = models.CharField(max_length=20)
    status_description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
  


    def __str__(self):
        return f'{self.user.username} - {self.timestamp}'
    
#class CampusDirectorHistoryCD(models.Model):
   # user = models.ForeignKey(User, on_delete=models.CASCADE)
   # start_date = models.DateField()
   # end_date = models.DateField()
   # description = models.TextField()

    #def __str__(self):
     #   return f'Campus Director History: {self.user.username}'

#class SupplyOfficeHistory(models.Model):
 #   start_date = models.DateField()
  #  end_date = models.DateField()
   # description = models.TextField()

    #def __str__(self):
     #   return f'Supply Office History: {self.start_date} to {self.end_date}'

#class SearchItem(models.Model):
#    title = models.CharField(max_length=200)
 #   description = models.TextField()
  #  link = models.URLField()
   # created_at = models.DateTimeField(default=timezone.now)


class PurchaseRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    item_name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.IntegerField()
    approved = models.BooleanField(default=False)
    disapproved = models.BooleanField(default=False)

    def __str__(self):
        return self.item_name
    
class PurchaseRequestHistory(models.Model):
    purchase_request = models.ForeignKey(PurchaseRequest, on_delete=models.CASCADE)
    action = models.CharField(max_length=20)
    timestamp = models.DateTimeField(auto_now_add=True)