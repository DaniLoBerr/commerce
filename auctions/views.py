from django import forms
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import *


# Forms
class NewBidForm(forms.Form):
    """Form for placing a new bid on a listing.
    
    :attr bid: The bid amount, displayed as a positive decimal number up
        to 10 digits and 2 decimal places with no label and a "Bid"
        placeholder.
    :type bid: DecimalField
    """
    bid = forms.DecimalField(
        decimal_places=2,
        label=False,
        max_digits=10,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "placeholder": "Bid",
            "class": "form-control mb-2",
        })
    )


class NewCommentForm(forms.Form):
    """Form for adding a new comment on a listing page.
    
    :attr title: The title of the comment, displayed as a single-line
        text input.
    :type title: CharField
    :attr message: The body of the comment, displayed as a multi-line
        textarea.
    :type message: CharField
    """
    title = forms.CharField(
        label="Title",
        max_length=100,
    )
    message = forms.CharField(
        label="Your comment",
        widget=forms.Textarea
    )


class NewListingForm(forms.Form):
    """Form for creating a new listing.
    
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


# Auth
def login_view(request):
    """Handle user login.
    
    On POST:
        - Retrieve the username and password from the form and attempt
        to authenticate the user.
        - If authentication is successful, log the user in and
        redirect them to the index page.
        - If authentication fails, re-render the login page with an
        error message.
    
    ON GET:
        - Render the login form page.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :return: HttpResponse redirecting to index page if login is
        successful, or rendering login page with error message.
    :rtype: HttpResponse
    """
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
            messages.error(request, "Invalid username and/or password.")
            return render(request, "auctions/login.html")

    return render(request, "auctions/login.html")


def logout_view(request):
    """Handle user logout.
    
    Call the logout function to log out the user associated with the
    request object.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :return: HttpResponse redirecting to index page.
    :rtype: HttpResponse
    """
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    """Handle user registration to the website.
    
    On POST:
        - Retrieve the username, email, password and confirmation from
        the registration form.
        - Ensure the password matches the confirmation; if not,
        re-render the registration form with an error massage.
        - Attempt to create a user object and save it to the database; 
        if the username is already taken, re-render the registration
        form with an error message.
        - If registration is successful, log in the user and redirect to
        the index page with a success message.

    On GET:
        - Render a page with the user registration form.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :return: HttpResponse that either render the registration form
        (on GET, or in case errors) or redirects to the index page
        (on successful registration).
    :rtype: HttpResponse
    """
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            messages.error(request, "Passwords must match.")
            return render(request, "auctions/register.html")

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            messages.error(request, "Username already taken.")
            return render(request, "auctions/register.html")
        login(request, user)
        messages.success(request, "Registration completed successfully.")
        return HttpResponseRedirect(reverse("index"))

    return render(request, "auctions/register.html")


# Auction listings
def index(request):
    """Render the main page displaying all active auction listings.
    
    :param request: The HTTP request object.
    :type request: HttpRequest
    :return: The HttpResponse containing the rendered index page.
    :rtype: HttpResponse
    """
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.prefetch_related("bids").all()
    })


def bid(request, listing_id):
    """Handle placing a new bid to a specific listing.
    
    Retrieve the listing object by its id, validate the bid form
    submitted by the user, and save the new bid if it meets the required
    conditions. The bid is accepted if:
    - If it's higher than the current biggest bid, or
    - There are no existing bids and the bid is at least equal to the
    listing's price.

    Depending on the outcome, success or error messages are displayed,
    and the user is redirected back to the listing page.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param listing_id: The id of the listing the user is bidding on.
    :type listing_id: int
    :return: An HttpResponseRedirect to the listing page.
    :rtype: HttpResponseRedirect
    """
    # Retrieve the listing the user is bidding on
    listing = Listing.objects.get(pk=listing_id)

    # Instantiate and validate the bid form with request data
    bid_form = NewBidForm(request.POST)
    if bid_form.is_valid():
        cleaned_bid = bid_form.cleaned_data["bid"]

        # Attempt to fetch the most recent bid for the listing
        try:
            last_bid = (
                Bid.objects
                    .filter(listing_id=listing_id)
                    .latest("datetime")
                    .value
            )
        except Bid.DoesNotExist:
            last_bid = None

        # Determine if the new bid is valid based on existing bids or listing
        # price
        if ((last_bid and cleaned_bid > last_bid)
        or (last_bid is None and cleaned_bid >= listing.price)):
            try:
                # Save the new valid bid
                new_bid = Bid(
                    value=cleaned_bid,
                    user=request.user,
                    listing=listing,
                )
                new_bid.save()
                messages.success(request, "Bid placed successfully.")
            except IntegrityError:
                messages.error(request, "Bid could not be placed.")
        else:
            messages.error(request, "Bid is not valid.")

    # Redirect the user back to the listing page
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))


def close(request):
    """Close a listing auction by its owner.

    Marks the listing as inactive and assigns the user with the most
    recent bid as the winner. Updates the database accordingly and
    provides a success or error message to the user.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :return: An HttpResponseRedirect to the listing page.
    :rtype: HttpResponseRedirect
    """
    # Retrieve the listing id from the query parameters
    listing_id = request.GET["listing_id"]

    # Get the listing object from the database
    listing = Listing.objects.get(pk=listing_id)

    # Attempt to assign the latest bidder as the winner and close the listing
    try:
        listing.winner = (
            Bid.objects
                .filter(listing_id=listing_id)
                .latest("datetime")
                .user
        )
        listing.is_active = False
        listing.save()
        messages.success(request, "Auction closed successfully")
    except (IntegrityError, Bid.DoesNotExist):
        messages.error(request, "Auction could not be closed")
    
    return HttpResponseRedirect(reverse("listing", args=[listing_id]))


def listing(request, id):
    """Render the page of a particular listing.
    
    Fetch the listing object, its related bids, and determines the
    latest bid value (or the initial listing price if no bids exist).
    Render the listing page with all necessary context data for display.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :param id: The id of the listing to display.
    :type id: int
    :return: The HttpResponse rendering the listing page.
    :rtype: HttpResponse
    """
    # Retrieve the selected listing object and all its related bids
    listing = Listing.objects.get(pk=id)
    listing_bids = Bid.objects.filter(listing_id=id)
    
    # Retrieve the value of the last listing bid or the listing price if
    # It has no related bids
    try:
        last_bid = listing_bids.latest("datetime").value
    except Bid.DoesNotExist:
        last_bid = listing.price

    return render(request, "auctions/listing.html", {
        "bids": len(listing_bids),
        "bid_form": NewBidForm(),
        "last_bid": last_bid,
        "listing": listing,
        "watchlist": Watchlist.objects.filter(
            listing_id=id,
            user_id=request.user.id,
        ),
    })


def new(request):
    """Handle creation of new auction listings.

    On POST:
        - Validate and process form data.
        - Create a new category if it does not exist.
        - Save the new listing.
        - Render the new listing page with a success message,
            or the index page with an error message if saving fails.

    On GET:
        - Render a page with a listing creation form.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :return: HttpResponse that either render the new listing form on
        GET, the index page in case error, or the new listing page on
        successful action.
    :rtype: HttpResponse
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
                messages.error(request, "Listing could not be saved.")
                return render(request, "auctions/index.html")

        # Render the new listing page with a success message
        messages.success(request, "Listing published successfully.")
        return HttpResponseRedirect(reverse("listing", args=[listing.id]))

    # If the view is accessed via GET
    return render(request, "auctions/new.html", {
        "form": NewListingForm()
    })


def watchlist(request):
    """Add or remove a listing from a user's watchlist
    
    Handle request to add or remove listings from a user's watchlist
    when the corresponding button is clicked on a listing page.

    Retrieve the user's id and the listing's id from the GET parameters.
    If the action is "add", add the listing to the user's watchlist.
    Otherwise, remove the listing from the user's watchlist. Raise an
    IntegrityError if these actions fail and display an error message.
    Redirect to the listing page in all cases.

    :param request: The HTTP request object.
    :type request: HttpRequest
    :return: HttpResponse redirecting to the listing page.
    :rtype: HttpResponse
    """
    # Get form parameters
    user_id = request.GET["user_id"]
    listing_id = request.GET["listing_id"]

    # Get objects from database
    user = User.objects.get(pk=user_id)
    listing = Listing.objects.get(pk=listing_id)
    
    if request.GET["action"] == "add":
        # Add listing to user's watchlist
        try:
            watchlist = Watchlist(
                user=user,
                listing=listing,
            )
            watchlist.save()
            messages.success(
                request, "Listing saved on your watchlist successfully."
            )
        except IntegrityError:
            messages.error(
                request, "Listing could not be saved on your watchlist."
            )
    else:
        # Remove listing from user's watchlist
        try:
            entry = Watchlist.objects.filter(
                user_id=user_id, listing_id=listing_id
            )
            entry.delete()
            messages.success(
                request, "Listing removed from your watchlist successfully."
            )
        except IntegrityError:
            messages.error(
                request, "Listing could not be removed from your watchlist."
            )

    return HttpResponseRedirect(reverse('listing', args=[listing_id]))