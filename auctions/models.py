from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model extending Django's AbstractUser.
    
    :attr address: Optional. Stores the user's address, up to 255
        characters.
    :type address: CharField
    :attr profile_image: Optional. Profile image for the user. Defaults
        to 'default-profile-image.png' if none is uploaded.
    :type profile_image: ImageField
    :attr phone_number: Optional. Stores the user's phone number, up to
        20 characters.
    :type phone_number: CharField 
    """
    address = models.CharField(blank=True, max_length=255)
    profile_image = models.ImageField(
        blank=True,
        default='default-profile-image.png',
        upload_to="profile_images/",
    )
    phone_number = models.CharField(blank=True, max_length=20)

    def __str__(self):
        """Return the full name of the user.
        
        :return: The user's full name in the format
            'first_name last_name'.
        :rtype: str
        """
        return f"{self.username}"


class Category(models.Model):
    """Represent a category to group multiple listings.
    
    :attr name: The name of the category, up to 64 characters.
    :type name: CharField
    """
    name = models.CharField(max_length=64)

    def __str__(self):
        """Return the name of the category.
        
        :return: The category's name.
        :rtype: str
        """
        return self.name


class Listing(models.Model):
    """Represent a listing for an item that can be posted by a user.
    
    :attr title: The title (name) of the listing, up to 100 characters.
    :type title: CharField
    :attr image: An uploaded image representing the listing.
    :type image: ImageField
    :attr description: A detailed description of the listing.
    :type description: TextField
    :attr price: Price of the listed item, stored with up to 10 digits
        and 2 decimal places.
    :type price: DecimalField
    :attr creation_date: Timestamp indicating when the listing was
        created, set automatically.
    :type creation_date: DateTimeField
    :attr is_active: Indicates whether the listing is active (True) or
        closed (False).
    :type is_active: BooleanField
    :attr winner: The user who placed the final bid; set to null if
        the user is deleted.
    :type winner: ForeignKey
    :attr category: The category to which this listing belongs.
        Deleting a category will delete all its associated listings.
    :type category: ForeignKey
    :attr owner: The user who created the listing. Deleting the user
        will also delete all their associated listings.
    :type owner: ForeignKey
    """
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to="listing_images/")
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    creation_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    winner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="listings",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="listings",
    )

    def __str__(self):
        """Return the title of the listing.
        
        :return: The title (name) of the listing.
        :rtype: str
        """
        return self.title


class Bid(models.Model):
    """Represent a bid placed by a user on a listing
    
    :attr value: The amount of the bid, up to 10 digits with 2 decimal
        places.
    :type value: DecimalField
    :attr datetime: Timestamp when the bid was placed, set
        automatically.
    :type datetime: DateTimeField
    :attr user: The user who placed the bid. Deleting the user removes
        their bids.
    :type user: ForeignKey
    :attr listing: The listing being bid on. Deleting the listing
        removes related bids.
    :type listing: ForeignKey
    """
    value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )
    datetime = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="bids",
    )

    def __str__(self):
        """Return a string containing the bid details.
        
        :return: A string in the format
            '{bid} by {user} on {listing}'
        :rtype: string
        """
        return f"${self.value} by {self.user} on {self.listing}"


class Comment(models.Model):
    """Represent a comment made by a user on a listing.
    
    :attr comment: The text content of the comment.
    :type comment: TextField
    :attr datetime: Timestamp when the comment was created, set
        automatically.
    :type datetime: DateTimeField
    :attr listing: The listing the comment is associated with. Deleting
        the listing removes related comments.
    :type listing: ForeignKey
    :attr user: The user who authored the comment. Deleting the user
        removes their comments.
    :type: listing: ForeignKey
    """
    comment = models.TextField()
    datetime = models.DateTimeField(auto_now_add=True)
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        """Return a string containing the comment details.
        
        :return: A string in the format
            'Comment by {user} on {listing}'.
        :rtype: str
        """
        return f"Comment by {self.user} on {self.listing}"


class Watchlist(models.Model):
    """Represent a user's watchlist entry for a specific listing.
    
    :attr user: The user who added the listing to their watchlist.
    :type user: ForeignKey
    :attr listing: The listing that the user added to their watchlist.
    :type listing: ForeignKey
    :attr created_at: Timestamp when the watchlist entry was added,
        set automatically.
    :type created_at: DateTimeField
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
    )
    listing = models.ForeignKey(
        Listing,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        """Return a string containing the details of a listing added to
        a user's watchlist at a particular timestamp.
        
        :return: A string in the format '{listing} added to {user}'s
            watchlist on {timestamp}"'.
        :rtype: str
        """
        return f"{self.listing} added to {self.user}'s watchlist on \
                {self.created_at}"