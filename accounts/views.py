from audioop import reverse
from io import BytesIO
import json
from pymongo import MongoClient
from urllib.parse import parse_qs
from django.views import View
from django.http import HttpResponseRedirect, JsonResponse
from typing import ItemsView
from django.shortcuts import redirect, render, get_object_or_404
from django.core.cache import cache
from accounts.forms import EditItemForm
from .models import *
import csv
from django.contrib.auth import authenticate, login as auth_login, logout
from .decorators import unauthenticated_user, authenticated_user
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.utils.encoding import force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.models import User
from django.http import HttpResponse  
from django.shortcuts import render, redirect   
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode  
from django.core.mail import EmailMessage 
from django.contrib.auth import get_user_model
from .tokens import account_activation_token
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.contrib import messages
from django.utils.crypto import get_random_string
from .models import VerificationCode
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from .models import Item
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import random
from django.shortcuts import render
from django.http import HttpResponse
import pdfkit

def main(request):
    return render(request, 'accounts/User/main.html')


def bac(request):
    return render(request, 'accounts/User/bac.html')

def homepage(request):
    return render(request, 'accounts/User/homepage.html')

User = get_user_model()
@unauthenticated_user
def register(request):
    if request.method == "POST":
        username = request.POST['username']
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        email = request.POST['email']
        contact1 = request.POST['contact1']
        contact2 = request.POST['contact2']
        password1 = request.POST['pass1']
        password2 = request.POST['pass2']
        user_type = request.POST['user_type']

        # Check if passwords match
        if password1 != password2:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/User/register.html')

        # Check if the username or email is already in use
        if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
            messages.error(request, "Username or email is already in use.")
            return render(request, 'accounts/User/register.html')

        # Create a new user account
        user = User.objects.create_user(username=username, email=email, password=password1, contact1=contact1, contact2=contact2,  user_type=user_type, is_active=False)
        user.first_name = first_name
        user.last_name = last_name
        user.save()

        # Send an activation email
        current_site = get_current_site(request)
        mail_subject = 'Activation link has been sent to your email id'
        message = render_to_string('accounts/User/acc_active_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        to_email = email
        email = EmailMessage(
            mail_subject, message, to=[to_email]
        )
        email.send()

        messages.success(request, "Your account has been successfully created. Check your email for activation instructions.")
        return redirect('login')  # Redirect to the login page upon successful registration
    return render(request, 'accounts/User/register.html')


def activate(request, uidb64, token):
    User = get_user_model()
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        return HttpResponse('Thank you for your email confirmation. Now you can log in to your account.')
    else:
        return HttpResponse('Activation link is invalid!')



def login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        pass1 = request.POST.get('pass1')  

        user = authenticate(request, username=username, password=pass1)
        if user is not None and user.is_active:
            auth_login(request, user)
            messages.success(request, "You are now logged in.")

            if user.user_type == 'admin':
                return redirect('bac_home')  
            else:
                return redirect('request')
        else:
            messages.error(request, "Invalid login credentials. Please try again.")
    return render(request, 'accounts/User/login.html')


def bac_home(request):
    if not request.user.is_admin:
        return redirect('request')
def request_page(request):
    if request.user.is_admin:
       
        return redirect('bac_home')
    
    
    return render(request, 'request.html')
def get_random_string(length, allowed_chars='0123456789'):
    return ''.join(random.choice(allowed_chars) for _ in range(length))


def handle_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        # Generate a random 4-digit verification code
        verification_code = get_random_string(4, '0123456789')
        
        # Store the verification code in the cache
        cache_key = f'verification_code_{email}'
        cache.set(cache_key, verification_code, 600)  # Store for 10 minutes (adjust as needed)
        
        # Send the verification code to the user's email
        subject = 'Password Reset Verification Code'
        message = f'Your verification code is: {verification_code}'
        from_email = 'rlphtzn@gmail.com'
        recipient_list = [email]

        send_mail(subject, message, from_email, recipient_list)
        
        # Redirect the user to a page where they can enter the verification code
        return redirect('verify_code')  # Make sure 'verify_code' is a valid URL pattern
    return render(request, 'accounts/User/forgot.html')



def verify_code(request):
    if request.method == 'POST':
        code1 = request.POST.get('code1')
        code2 = request.POST.get('code2')
        code3 = request.POST.get('code3')
        code4 = request.POST.get('code4')

        verification_code = f"{code1}{code2}{code3}{code4}"
        user_email = request.POST.get('email')
        if is_valid_code(verification_code, user_email):
            return redirect('reset_password')  # Make sure 'reset_password' is a valid URL pattern
    return render(request, 'accounts/User/verify.html')  # Make sure the template exists


def is_valid_code(verification_code, user_email):
    # Construct the cache key based on the user's email
    cache_key = f'verification_code_{user_email}'
    
    # Retrieve the stored verification code from the cache
    stored_code = cache.get(cache_key)
    
    if stored_code and verification_code == stored_code:
        # Codes match, and the code exists in the cache
        return True
    return False


 # You can use this decorator to ensure the user is logged in to reset their password
def reset_password(request):
    if request.method == 'POST':
        # Handle the password reset form submission here
        new_password = request.POST.get('new_password')  # Assuming you have a form field with name="new_password"
        
        # Update the user's password securely
        user = request.user  # Get the current logged-in user
        
        # Set the new password for the user
        user.set_password(new_password)
        
        # Save the user to update the password in the database
        user.save()
        
        # To maintain the user's session after changing the password, you can use the following:
        update_session_auth_hash(request, user)
        
        # Redirect the user to a success page or login page
        messages.success(request, 'Password updated successfully.')
        return redirect('login')  # Change 'login' to the name of your login URL pattern
    return render(request, 'accounts/User/reset.html')  # Adjust the template name as needed

@authenticated_user
def logout_user(request):
    logout(request)
    messages.success(request, ("You are now successfully logout."))
    return redirect('homepage')


@authenticated_user
def about(request):
    return render(request, 'accounts/User/about.html')


@authenticated_user
@authenticated_user
def registration(request):
    return render(request, 'accounts/User/registration.html')


@authenticated_user
def history(request):
    # Get the logged-in user
    user = request.user

    # Get all checkouts for the logged-in user
    all_checkouts = Checkout.objects.filter(user=user)

    # Get checkout items associated with all checkouts
    all_checkout_items = CheckoutItems.objects.filter(checkout__in=all_checkouts)

    context = {
        'checkout_items': all_checkout_items,
    }

    return render(request, 'accounts/User/history.html', context)


@authenticated_user
def tracker(request):
    user = request.user


    all_checkouts = Checkout.objects.filter(user=user)


    feedback = Comment.objects.filter(pr_id__in=[checkout.pr_id for checkout in all_checkouts])
                                                

    context = {'feedback': feedback, 'checkout_info': all_checkouts}
    return render(request, 'accounts/User/tracker.html', context)


@authenticated_user
def prof(request):
    return render(request, 'accounts/User/prof.html')


@authenticated_user
def profile(request):
    return render(request, 'accounts/User/profile.html')


@authenticated_user
def bac_about(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/bac_about.html')


@authenticated_user
def bac_home(request):
    checkouts = Checkout.objects.select_related('user').all()
    comments = Comment.objects.all()

    # Create a dictionary to store the results, using pr_id as keys
    checkout_data_dict = {}

    # Loop through each Checkout instance and gather relevant data
    for checkout in checkouts:
        pr_id = checkout.pr_id

        # Get the latest comment for the current pr_id
        latest_comment = comments.filter(pr_id=pr_id).order_by('-timestamp').first()

        if pr_id not in checkout_data_dict:
            # If pr_id is not in the dictionary, create a new entry
            checkout_data_dict[pr_id] = {
                'pr_id': pr_id,
                'first_name': checkout.user.first_name,
                'last_name': checkout.user.last_name,
                'submission_date': checkout.submission_date,
                'purpose': checkout.purpose,
                'status_comment': latest_comment.content if latest_comment else "",
                'status_update_date': latest_comment.timestamp if latest_comment else None,
                # Add more fields as needed
            }
        else:
            # If pr_id is already in the dictionary, update the entry
            # with additional information, e.g., concatenate purposes
            checkout_data_dict[pr_id]['purpose'] += f", {checkout.purpose}"

    # Convert the dictionary values to a list
    checkout_data = list(checkout_data_dict.values())

    return render(request, 'accounts/Admin/BAC_Secretariat/bac_home.html', {'checkouts': checkout_data})


from django.urls import reverse

# ...

class PreqFormView(View):
    template_name = 'accounts/Admin/BAC_Secretariat/preqform.html'

    def get(self, request, pr_id):
        # Use the pr_id to retrieve the corresponding Checkout object
        checkout = Checkout.objects.get(pr_id=pr_id)

        # Get checkout items associated with the checkout
        checkout_items = CheckoutItems.objects.filter(checkout=checkout)

        context = {
            'checkout_items': checkout_items,
            'pr_id': pr_id,
            'user': checkout.user,
            'purpose': checkout.purpose,
        }

        return render(request, self.template_name, context)

    def post(self, request, pr_id):
        # Access the pr_id and content from the POST data
        content = request.POST.get('comment_content')

        # Check if both pr_id and content are present
        if pr_id and content:
            try:
                # Save the comment with the pr_id directly
                Comment.objects.create(content=content, timestamp=timezone.now(), pr_id=pr_id)

                # Redirect after processing
                return redirect(reverse('preqform', kwargs={'pr_id': pr_id}))
            except Exception as e:
                # Handle exceptions, log errors, etc.
                print(f"Error: {e}")
                return HttpResponse("An error occurred while processing the form.")
        else:
            return HttpResponse("PR ID or comment content not found in the form data.")
        

@authenticated_user
def np(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/np.html')


@authenticated_user
def purchaseorder(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/purchaseorder.html')


@authenticated_user
def bids(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/bids.html')


@authenticated_user
def noa(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/noa.html')


@authenticated_user
def purchaseorder(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/purchaseorder.html')



@authenticated_user
def inspection(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/inspection.html')


@authenticated_user
def property(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/property.html')


@authenticated_user
def np(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/np.html')


@authenticated_user
def notif(request):
    return render(request, 'accounts/Admin/BAC_Secretariat/notif.html')


@authenticated_user
def abstract(request):
    # Your view logic here
    return render(request, 'accounts/Admin/BAC_Secretariat/abstract.html')


@authenticated_user
def bo(request):
    return render(request, 'accounts/Admin/Budget_Officer/bo.html')


@authenticated_user
def boabout(request):
    return render(request, 'accounts/Admin/Budget_Officer/boabout.html')


@authenticated_user
def bohistory(request):
    return render(request, 'accounts/Admin/Budget_Officer/bohistory.html')


@authenticated_user
def cd(request):
    return render(request, 'accounts/Admin/Campus_Director/cd.html')


@authenticated_user
def cdabout(request):
    return render(request, 'accounts/Admin/Campus_Director/cdabout.html')


@authenticated_user
def cdhistory(request):
    return render(request, 'accounts/Admin/Campus_Director/cdhistory.html')


@authenticated_user
def cdresolution(request):
    return render(request, 'accounts/Admin/Campus_Director/cdresolution.html')


@authenticated_user
def profile_html(request):
    return render(request, 'profile.html')


def addItem(request):
    if request.method == 'POST':
        item_data = request.POST.get('item')
        item_brand_description = request.POST.get('item_Brand_Description')
        unit = request.POST.get('unit')
        unit_cost = request.POST.get('unit_Cost')
        quantity = request.POST.get('quantity')

        user = request.user

    
        Item.objects.create(
            user=user,
            item=item_data,
            item_brand_description=item_brand_description,
            unit=unit,
            unit_cost=unit_cost,
            quantity=quantity,
             # Calculate total cost based on price and quantity
        )
        
        return redirect('request')
    return render(request, 'accounts/User/request.html')



def request(request):
    if request.method == 'POST':
        # Retrieve selected rows from the form
        selected_rows = request.POST.getlist('selectRow')

        # Process and save data to the database
        for row_id in selected_rows:
            item_name = request.POST.get(f'item_{row_id}')
            item_brand = request.POST.get(f'item_brand_{row_id}')
            unit = request.POST.get(f'unit_{row_id}')
            price = request.POST.get(f'price_{row_id}')
            quantity = request.POST.get(f'quantity_{row_id}')

            user = request.user

            # Save the data to the CartItem model (update this based on your model)
            items = Item.objects.create(
                user=user,
                item=item_name,
                item_brand_description=item_brand,
                unit=unit,
                unit_cost=price,
                quantity=quantity,
                 # Calculate total cost based on price and quantity
            )
            items.save()

        # Redirect to a success page
        return redirect('requester')

    else:
        # Handle data fetching for GET request
        # Connect to MongoDB
        csv_file_path ='C:/Users/maceda.danicamae/Documents/MACEDA DANICA MAE D/INVENTORY/ONLINE_SUPPLY_OFFICE_COPY/items.csv'
        with open(csv_file_path, 'r') as file:
            reader = csv.DictReader(file)
            csv_data = list(reader)
        
        # Pass data to the template
        return render(request, 'accounts/User/request.html', {'csv_data': csv_data})


    


class RequesterView(View):
    template_name = 'accounts/User/cart.html'

    def get(self, request):
         # Fetch data from the Item model and pass it to the template
        items = Item.objects.all()

        # Calculate total cost based on the items
        # ...
        return render(request, self.template_name, {'items': items})

    def post(self, request):
        if request.method == 'POST':
            # Fetch data from the Item model
            items = Item.objects.all()

            # Handle form submission
            purpose = request.POST.get('purpose', '')  # Retrieve the 'Purpose' value
           

            new_checkout = Checkout.objects.create(user=request.user, pr_id=self.generate_pr_id(), purpose=purpose)

            for row in items:
                item_id = row.id
                item = request.POST.get(f'item_{item_id}')
                item_brand = request.POST.get(f'item_brand_{item_id}')
                unit = request.POST.get(f'unit_{item_id}')
                quantity = int(request.POST.get(f'quantity_{item_id}', 0)) 
                price = Decimal(request.POST.get(f'price_{item_id}', '0.00')) 

                try:
                    total_cost = price * quantity
                except TypeError:
                    total_cost = Decimal('0.00')

                # Customize the fields according to your CheckoutItems model
                CheckoutItems.objects.create(
                    checkout=new_checkout,
                    item=item,
                    item_brand_description=item_brand,
                    unit=unit,
                    quantity=quantity,
                    unit_cost=price,
                    total_cost=total_cost,  # Calculate total cost based on the price and quantity
                    # Add other fields as needed
                )
                new_checkout.save()
                items.delete()

            return redirect('history')
        
    def generate_pr_id(self):
        random_number = str(random.randint(10000000, 99999999))

        return f"{random_number}_{timezone.now().strftime('%Y%m%d%H%M%S')}"



@authenticated_user
def item_list(request):
    items = Item.objects.all()
    return render(request, 'item_list.html', {'items': items})


@authenticated_user
def item_list(request):
    items = Item.objects.all()
    return render(request, 'item_list.html', {'items': items})



@authenticated_user
def show_more_details(request):
    if request.method == 'POST':
        request_id = request.POST.get('request_id', None)

        if request_id:
            # Fetch the relevant data based on request_id
            # You should replace this with your actual data retrieval logic

            # For demonstration purposes, let's assume you have a dictionary
            # with form_type and form_data
            form_type = request.POST.get('form_type', 'other')
            form_data = {
                'purchase_approval': {'field1': 'Value1', 'field2': 'Value2'},
                'resolution_approval': {'field3': 'Value3', 'field4': 'Value4'},
                'abstract_of_bids': {'field5': 'Value5', 'field6': 'Value6'},
                'notice_of_reward': {'field7': 'Value7', 'field8': 'Value8'},
                'notice_to_proceed': {'field9': 'Value9', 'field10': 'Value10'},
                'inspection_acceptance': {'field11': 'Value11', 'field12': 'Value12'},
                'property_acknowledgment': {'field13': 'Value13', 'field14': 'Value14'},
                'purchase_order': {'field15': 'Value15', 'field16': 'Value16'},
            }

            response_data = form_data.get(form_type, {})
            return JsonResponse(response_data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@authenticated_user
def bac_history(request):
   request = Item.objects.all()

   return render(request,  'accounts/Admin/BAC_Secretariat/bac_history.html', {'request': request})


class GetNewRequestsView(View):
    def get(self, request, *args, **kwargs):

       

          # Fetch new requests from the database based on your criteria
        new_requests = Checkout.objects.exclude(pr_id=None)

        # Serialize the data as needed
        serialized_requests = [
            {
                'user_id': request.user_id,
                'submission_date': request.submission_date,
                # Add other fields as needed
            }
            for request in new_requests
        ]

        return JsonResponse({'new_requests': serialized_requests})
    

# @authenticated_user
# def item_delete(request, request_id):
#     item = get_object_or_404(Item, request_id=request_id)
#     item.delete()
#     # Redirect to an appropriate URL after deletion
#     return redirect('requester')  # Replace 'requester' with your desired redirect URL name


def view_cart(request, id):
    item = Item.objects.get(id = id)

    return render (request, { 'item': item})



def edit_item(request, id):
    edit = Item.objects.get(id=id)

    if request.method == "POST":
        # Update the item fields with the new data from the request
        item_name = request.POST.get('item_name')
        item_description = request.POST.get('item_description')
        unit = request.POST.get('item_unit')
        unit_cost = request.POST.get('item_unit_cost')
        quantity = request.POST.get('item_quantity')
        total_cost = request.POST.get('item_total_cost')

        # Update the existing 'edit' item with the new data
        edit.item = item_name
        edit.item_brand_description = item_description
        edit.unit = unit
        edit.unit_cost = unit_cost
        edit.quantity = quantity
        edit.total_cost = total_cost
        edit.save()


    return render(request, 'requester', {'edit': edit})
                  
def delete_item(request, id):
    item = Item.objects.get(id = id)
    item.delete()
    return redirect ('requester')

def connect_to_mongo():
    client = MongoClient("mongodb://localhost:27017/")  # Update the connection string accordingly
    database = client["inventory"]
    collection = database["inventorycol"]
    return collection



def bac_dashboard(request):
    if request.method == 'POST':
        category = request.POST.get('category')  # Corrected from 'catgory'
        item_name = request.POST.get('item_name')  # Corrected name
        item_brand_description = request.POST.get('item_brand')
        unit = request.POST.get('unit')
        unit_cost = request.POST.get('price')  # Corrected name

        insert_data = {
            "Category": category,
            "Item_name": item_name,
            "Item_brand": item_brand_description,
            "Unit": unit,
            "Price": unit_cost
            
        }
        collection = connect_to_mongo()
        collection.insert_one(insert_data)
        
        return redirect('bac_dashboard')
    
   

    elif request.method == 'GET':
        # Handling GET request to retrieve data
        collection = connect_to_mongo()
        items = collection.find()

        # Convert the cursor to a list
        item_list = list(items)

        # Pass the data to the template
        return render(request, 'accounts/Admin/BAC_Secretariat/bac_dashboard.html', {'items': item_list})
    
    return render(request, 'accounts/Admin/BAC_Secretariat/bac_dashboard.html')
