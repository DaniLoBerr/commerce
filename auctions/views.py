from django import forms
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import *


class NewListingForm(forms.Form):
    """Form for creating a new listing. Extends forms.Form.
    
    :attr title: The title of the listing, displayed as a single-line
        text input with a "Title" label.
    :type title: CharField
    :attr description: The description of the listing, displayed as a
        multi-line textarea with a "Description" label.
    :type description: CharField
    :attr starting_bid: The starting bid amount, displayed as a positive
        decimal number up to 10 digits and 2 decimal places with a
        "Starting bid" label.
    :type starting_bid: DecimalField
    :attr image: An image associated with the listing with a
        "Listing image" label.
    :type image: ImageField
    :attr category: The category of the listing, displayed as a
        single-line text input with a "Category" label.
    :type category: CharField
    """
    title = forms.CharField(label="Title")
    description = forms.CharField(
        label="Description",
        widget=forms.Textarea(),
    )
    starting_bid = forms.DecimalField(
        decimal_places=2,
        label="Starting bid",
        max_digits=10,
        min_value=0,
    )
    image = forms.ImageField(label="Listing image")
    category = forms.CharField(label="Category")


def index(request):
    return render(request, "auctions/index.html")


# auth
def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


# listings
def new(request):
    """Handle creation of new auction listings.

    On POST:
        - Validates and processes form data.
        - Creates a new category if it does not exist.
        - Saves the new listing.
        - Renders the index page with a success message,
            or with an error message if saving fails.

    On GET:
        - Renders a page with a listing creation form.
    """
    if request.method == "POST":

        # Bind form data and files
        form = NewListingForm(request.POST, request.FILES)

        if form.is_valid():
            # Clean form data
            cleaned_title = form.cleaned_data["title"]
            cleaned_image = form.cleaned_data["image"]
            cleaned_description = form.cleaned_data["description"]
            cleaned_bid = form.cleaned_data["starting_bid"]
            cleaned_category = form.cleaned_data["category"]

            # Save new category or get an object of the existing one
            try:
                category = Category.objects.get(name__iexact=cleaned_category)
            except Category.DoesNotExist:
                category = Category(name=cleaned_category)
                category.save()

            # Save new listing or show an error message if saving fails
            try:
                listing = Listing(
                    title=cleaned_title,
                    image=cleaned_image,
                    description=cleaned_description,
                    price=cleaned_bid,
                    category=category,
                    owner=request.user
                )
                listing.save()
            except IntegrityError:
                return render(request, "auctions/index.html", {
                    "message": "Listing could not be saved"
                })
            
        #TODO: render the new listing page and update docstring
        return render(request, "auctions/index.html", {
                    "message": "Listing published successfully"
                })

    # If the view is accessed via GET
    return render(request, "auctions/new.html", {
        "form": NewListingForm()
    })