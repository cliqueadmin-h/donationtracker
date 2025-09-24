#!/usr/bin/env python3
"""
Updated Donation Opportunities Finder using Google Places API (New)

This version uses the new Google Places API which is the recommended approach.
"""

import os
import json
import time
import math
import re
from typing import List, Dict, Any, Optional
import requests


class DonationFinderNew:
    """Class to find donation opportunities using Google Places API (New)"""
    
    # Using the new Places API
    BASE_URL = "https://places.googleapis.com/v1/places:searchText"
    PLACE_DETAILS_URL = "https://places.googleapis.com/v1/places/{place_id}"
    
    # Rate limiting configuration
    SEARCH_API_DELAY = 1.2  # Seconds between search API calls
    DETAILS_API_DELAY = 0.8  # Seconds between place details API calls  
    EMAIL_SCRAPE_DELAY = 0.6  # Seconds between website email scraping
    
    # Default keywords for finding donation opportunities
    DEFAULT_KEYWORDS = [
        "charity near me",
        "NGO near me", 
        "food bank near me",
        "shelter near me",
        "orphanage near me",
        "donation center near me",
        "blood bank near me",
        "homeless shelter near me",
        "soup kitchen near me",
        "community center near me",
        "nonprofit organization near me",
        "animal shelter near me",
        "salvation army near me",
        "red cross near me"
    ]
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the DonationFinderNew
        
        Args:
            api_key: Google Maps API key. If None, will try to get from environment
        """
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError("Google Maps API key is required. Set GOOGLE_MAPS_API_KEY environment variable or pass api_key parameter.")
        
        # Rate limiting tracking
        self.last_search_call = 0
        self.last_details_call = 0
        self.total_api_calls = 0
        
        self.session = requests.Session()
        # Set up headers for the new API
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': 'places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.businessStatus,places.types,places.priceLevel,places.userRatingCount'
        })
    
    def extract_email_from_website(self, website_url: str) -> str:
        """
        Attempt to extract email address from website content
        
        Args:
            website_url: URL to search for email addresses
            
        Returns:
            Email address if found, empty string otherwise
        """
        if not website_url or not website_url.startswith(('http://', 'https://')):
            return ''
        
        try:
            # Create a separate session for web scraping with different headers
            scrape_session = requests.Session()
            scrape_session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            })
            
            # Set a short timeout to avoid long waits
            response = scrape_session.get(website_url, timeout=5)
            response.raise_for_status()
            
            # Look for email patterns in the HTML content
            content = response.text.lower()
            
            # Common email patterns for organizations
            email_patterns = [
                r'mailto:([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
                r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            ]
            
            for pattern in email_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    # Return the first valid email found
                    email = matches[0] if isinstance(matches[0], str) else matches[0]
                    # Filter out common non-contact emails
                    excluded_emails = ['noreply@', 'no-reply@', 'donotreply@', 'support@google', 'webmaster@', 'admin@', 'postmaster@']
                    if not any(excluded in email.lower() for excluded in excluded_emails):
                        return email
            
            return ''
            
        except (requests.exceptions.RequestException, requests.exceptions.Timeout):
            # Don't print errors for email extraction as it's supplementary
            return ''
        except Exception:
            return ''
    
    def _enforce_rate_limit(self, api_type: str = 'search'):
        """
        Enforce rate limiting for API calls
        
        Args:
            api_type: Type of API call ('search' or 'details')
        """
        current_time = time.time()
        
        if api_type == 'search':
            time_since_last = current_time - self.last_search_call
            required_delay = self.SEARCH_API_DELAY
            if time_since_last < required_delay:
                sleep_time = required_delay - time_since_last
                print(f"  ⏱️  Rate limiting: waiting {sleep_time:.1f}s before search API call")
                time.sleep(sleep_time)
            self.last_search_call = time.time()
            
        elif api_type == 'details':
            time_since_last = current_time - self.last_details_call
            required_delay = self.DETAILS_API_DELAY
            if time_since_last < required_delay:
                sleep_time = required_delay - time_since_last
                print(f"  ⏱️  Rate limiting: waiting {sleep_time:.1f}s before details API call")
                time.sleep(sleep_time)
            self.last_details_call = time.time()
        
        self.total_api_calls += 1
        if self.total_api_calls % 10 == 0:
            print(f"  📊 Total API calls made: {self.total_api_calls}")
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the distance between two points using Haversine formula
        
        Args:
            lat1, lon1: Latitude and longitude of first point
            lat2, lon2: Latitude and longitude of second point
            
        Returns:
            Distance in meters
        """
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in meters
        r = 6371000
        return c * r
    
    def search_places(self, latitude: float, longitude: float, radius: int, keyword: str, min_rating: float = 0.0) -> List[Dict[str, Any]]:
        """
        Search for places using Google Places API (New)
        
        Args:
            latitude: Latitude of search center
            longitude: Longitude of search center
            radius: Search radius in meters
            keyword: Keyword to search for
            min_rating: Minimum rating filter
            
        Returns:
            List of places found
        """
        places = []
        
        print(f"Searching for '{keyword}' within {radius}m of {latitude},{longitude}...")
        
        # Enforce rate limiting before making the API call
        self._enforce_rate_limit('search')
        
        # Create the request body for the new API
        request_body = {
            "textQuery": keyword,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": radius
                }
            },
            "maxResultCount": 20
        }
        
        try:
            response = self.session.post(self.BASE_URL, json=request_body)
            response.raise_for_status()
            data = response.json()
            
            results = data.get('places', [])
            
            # Filter by distance manually to ensure accuracy
            filtered_results = []
            for place in results:
                location = place.get('location', {})
                if location.get('latitude') and location.get('longitude'):
                    distance = self.calculate_distance(
                        latitude, longitude,
                        location['latitude'], location['longitude']
                    )
                    if distance <= radius:
                        # Filter by minimum rating if specified
                        rating = place.get('rating', 0)
                        if rating >= min_rating:
                            filtered_results.append(place)
            
            places.extend(filtered_results)
                    
        except requests.exceptions.RequestException as e:
            print(f"Request error for keyword '{keyword}': {e}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error for keyword '{keyword}': {e}")
        except Exception as e:
            print(f"Unexpected error for keyword '{keyword}': {e}")
        
        print(f"Found {len(places)} places for keyword '{keyword}'")
        return places
    
    def get_place_details_with_reviews(self, place_id: str, max_reviews: int = 5) -> Dict[str, Any]:
        """
        Get detailed information about a place including user reviews
        
        Args:
            place_id: Google Places place ID
            max_reviews: Maximum number of reviews to fetch (default: 5)
            
        Returns:
            Dictionary containing place details and reviews
        """
        # Define what fields we want to get (including email if available)
        field_mask = "id,displayName,formattedAddress,rating,userRatingCount,reviews,photos,regularOpeningHours,internationalPhoneNumber,websiteUri,businessStatus,editorialSummary"
        
        headers = {
            'Content-Type': 'application/json',
            'X-Goog-Api-Key': self.api_key,
            'X-Goog-FieldMask': field_mask
        }
        
        url = self.PLACE_DETAILS_URL.format(place_id=place_id)
        
        # Enforce rate limiting before making the API call
        self._enforce_rate_limit('details')
        
        try:
            print(f"Fetching details for place: {place_id}")
            response = self.session.get(url, headers=headers)
            response.raise_for_status()
            place_data = response.json()
            
            # Process reviews if available
            reviews = []
            if 'reviews' in place_data:
                for review in place_data['reviews'][:max_reviews]:
                    processed_review = {
                        'author_name': review.get('authorAttribution', {}).get('displayName', 'Anonymous'),
                        'author_photo': review.get('authorAttribution', {}).get('photoUri', ''),
                        'rating': review.get('rating', 0),
                        'text': review.get('text', {}).get('text', ''),
                        'time_description': review.get('relativePublishTimeDescription', ''),
                        'publish_time': review.get('publishTime', '')
                    }
                    reviews.append(processed_review)
            
            # Process opening hours if available
            opening_hours = []
            if 'regularOpeningHours' in place_data:
                hours = place_data['regularOpeningHours']
                if 'weekdayDescriptions' in hours:
                    opening_hours = hours['weekdayDescriptions']
            
            # Extract website URL for email extraction
            website_url = place_data.get('websiteUri', '')
            
            # Try to extract email from website (with rate limiting)
            email = ''
            if website_url:
                print(f"  🔍 Extracting email from website: {website_url}")
                email = self.extract_email_from_website(website_url)
                if email:
                    print(f"  ✅ Found email: {email}")
                else:
                    print(f"  ❌ No email found")
                # Add a delay to be respectful to websites
                time.sleep(self.EMAIL_SCRAPE_DELAY)
            
            return {
                'place_id': place_data.get('id', place_id),
                'name': place_data.get('displayName', {}).get('text', ''),
                'formatted_address': place_data.get('formattedAddress', ''),
                'rating': place_data.get('rating', 0),
                'user_ratings_total': place_data.get('userRatingCount', 0),
                'reviews': reviews,
                'opening_hours': opening_hours,
                'phone': place_data.get('internationalPhoneNumber', ''),
                'website': place_data.get('websiteUri', ''),
                'email': email,
                'business_status': place_data.get('businessStatus', 'UNKNOWN'),
                'photos_available': len(place_data.get('photos', [])),
                'review_count': len(reviews)
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Request error fetching place details: {e}")
            return {'error': f"Request error: {e}"}
        except json.JSONDecodeError as e:
            print(f"JSON decode error fetching place details: {e}")
            return {'error': f"JSON decode error: {e}"}
        except Exception as e:
            print(f"Unexpected error fetching place details: {e}")
            return {'error': f"Unexpected error: {e}"}
    
    def enhance_places_with_reviews(self, places: List[Dict[str, Any]], max_reviews: int = 3, include_all: bool = False) -> List[Dict[str, Any]]:
        """
        Enhance places list with detailed reviews and additional information
        
        Args:
            places: List of places from search results
            max_reviews: Maximum reviews per place (default: 3)
            include_all: If True, get reviews for all places. If False, only for top-rated (default: False)
            
        Returns:
            Enhanced list of places with reviews
        """
        enhanced_places = []
        
        print(f"\n📝 Fetching detailed reviews for places...")
        
        for i, place in enumerate(places):
            print(f"Processing {i+1}/{len(places)}: {place.get('name', 'Unknown')}")
            
            # Skip getting reviews for low-rated places unless include_all is True
            rating = place.get('rating', 0) or 0  # Handle None ratings
            if not include_all and rating < 3.0:
                print(f"  Skipping reviews for low-rated place (rating: {rating})")
                enhanced_place = place.copy()
                enhanced_place['reviews'] = []
                enhanced_place['detailed_info_fetched'] = False
                enhanced_places.append(enhanced_place)
                continue
            
            place_id = place.get('id') or place.get('place_id')
            if not place_id:
                print(f"  No place_id found for {place.get('name', 'Unknown')}")
                enhanced_place = place.copy()
                enhanced_place['reviews'] = []
                enhanced_place['detailed_info_fetched'] = False
                enhanced_places.append(enhanced_place)
                continue
            
            # Get detailed information including reviews
            details = self.get_place_details_with_reviews(place_id, max_reviews)
            
            if 'error' in details:
                print(f"  Error fetching details: {details['error']}")
                enhanced_place = place.copy()
                enhanced_place['reviews'] = []
                enhanced_place['detailed_info_fetched'] = False
                enhanced_places.append(enhanced_place)
                continue
            
            # Merge original place data with detailed information
            enhanced_place = place.copy()
            enhanced_place.update({
                'reviews': details.get('reviews', []),
                'opening_hours': details.get('opening_hours', []),
                'phone': details.get('phone', ''),
                'website': details.get('website', ''),
                'email': details.get('email', ''),
                'business_status': details.get('business_status', 'UNKNOWN'),
                'photos_available': details.get('photos_available', 0),
                'review_count': details.get('review_count', 0),
                'user_ratings_total': details.get('user_ratings_total', 0),
                'detailed_info_fetched': True
            })
            
            print(f"  ✅ Added {len(details.get('reviews', []))} reviews")
            enhanced_places.append(enhanced_place)
            
            # Rate limiting is now handled by _enforce_rate_limit method
        
        print(f"📝 Enhanced {len(enhanced_places)} places with detailed information")
        return enhanced_places
    
    def process_places(self, places: List[Dict[str, Any]], origin_lat: float, origin_lng: float) -> List[Dict[str, Any]]:
        """
        Process and format places data from the new API format
        
        Args:
            places: Raw places data from API
            origin_lat, origin_lng: Origin coordinates for distance calculation
            
        Returns:
            Processed and formatted places data
        """
        processed_places = []
        
        for place in places:
            location = place.get('location', {})
            
            # Calculate distance from origin
            distance = 0
            if location.get('latitude') and location.get('longitude'):
                distance = self.calculate_distance(
                    origin_lat, origin_lng,
                    location['latitude'], location['longitude']
                )
            
            processed_place = {
                'name': place.get('displayName', {}).get('text', 'Unknown'),
                'address': place.get('formattedAddress', 'No address available'),
                'place_id': place.get('id', ''),
                'latitude': location.get('latitude'),
                'longitude': location.get('longitude'),
                'rating': place.get('rating'),
                'business_status': place.get('businessStatus', '').replace('BUSINESS_STATUS_', ''),
                'types': place.get('types', []),
                'price_level': place.get('priceLevel'),
                'user_ratings_total': place.get('userRatingCount'),
                'distance_meters': round(distance, 2),
                'distance_km': round(distance / 1000, 2),
                'permanently_closed': place.get('businessStatus') == 'BUSINESS_STATUS_PERMANENTLY_CLOSED'
            }
            
            processed_places.append(processed_place)
        
        return processed_places
    
    def deduplicate_places(self, places: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Remove duplicate places based on place_id
        
        Args:
            places: List of places
            
        Returns:
            Deduplicated list of places
        """
        seen_place_ids = set()
        unique_places = []
        
        for place in places:
            place_id = place.get('place_id', '')
            if place_id and place_id not in seen_place_ids:
                seen_place_ids.add(place_id)
                unique_places.append(place)
            elif not place_id:
                # Keep places without place_id (shouldn't happen with Google API but just in case)
                unique_places.append(place)
        
        return unique_places
    
    def find_donation_opportunities(self, 
                                  latitude: float, 
                                  longitude: float,
                                  radius: int = 5000,
                                  keywords: Optional[List[str]] = None,
                                  min_rating: float = 0.0,
                                  sort_by_distance: bool = True) -> List[Dict[str, Any]]:
        """
        Find donation opportunities near the specified location
        
        Args:
            latitude: Latitude of search center
            longitude: Longitude of search center
            radius: Search radius in meters (default: 5000)
            keywords: List of keywords to search for (default: DEFAULT_KEYWORDS)
            min_rating: Minimum rating filter (default: 0.0, no filter)
            sort_by_distance: Sort results by distance (default: True)
            
        Returns:
            List of donation opportunities
        """
        if keywords is None:
            keywords = self.DEFAULT_KEYWORDS
        
        all_places = []
        
        print(f"Searching for donation opportunities near {latitude},{longitude}")
        print(f"Radius: {radius}m, Min Rating: {min_rating}")
        print(f"Keywords: {', '.join(keywords)}")
        print("-" * 60)
        
        # Search for each keyword
        for keyword in keywords:
            places = self.search_places(latitude, longitude, radius, keyword, min_rating)
            all_places.extend(places)
            
            # Rate limiting is now handled by _enforce_rate_limit method
        
        print("-" * 60)
        print(f"Total places found: {len(all_places)}")
        
        # Process places
        processed_places = self.process_places(all_places, latitude, longitude)
        
        # Remove duplicates
        unique_places = self.deduplicate_places(processed_places)
        print(f"Unique places after deduplication: {len(unique_places)}")
        
        # Filter out permanently closed places
        active_places = [place for place in unique_places if not place.get('permanently_closed', False)]
        print(f"Active places (not permanently closed): {len(active_places)}")
        
        # Sort by distance if requested
        if sort_by_distance:
            active_places.sort(key=lambda x: x.get('distance_meters', float('inf')))
        
        return active_places
    
    def save_to_json(self, places: List[Dict[str, Any]], filename: str = "donation_opportunities.json"):
        """
        Save results to JSON file
        
        Args:
            places: List of places to save
            filename: Output filename (default: donation_opportunities.json)
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(places, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {filename}")
        except Exception as e:
            print(f"Error saving to JSON: {e}")