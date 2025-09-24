#!/usr/bin/env python3
"""
Simple zip code search with coordinate mapping

This version uses a pre-built coordinate mapping for common zip codes
to perform more accurate location-based searches.
"""

import json
import os
from donation_finder import DonationFinderNew

class SimpleZipCodeFinder:
    def __init__(self, api_key):
        self.finder = DonationFinderNew(api_key)
        self.zip_coordinates = self._load_zip_coordinates()
    
    def _load_zip_coordinates(self):
        """Load zip code to coordinate mapping"""
        try:
            with open('zip_coordinates.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print("Warning: zip_coordinates.json not found. Using fallback method.")
            return {}
    
    def search_by_zip(self, zip_code, keywords, max_results=20, radius=5000):
        """
        Search for donation opportunities by zip code.
        Uses coordinates if available, otherwise falls back to text search.
        """
        print(f"Searching for donation opportunities in zip code: {zip_code}")
        print(f"Keywords: {', '.join(keywords)}")
        
        # Check if we have coordinates for this zip code
        if zip_code in self.zip_coordinates:
            zip_info = self.zip_coordinates[zip_code]
            lat, lng = zip_info['lat'], zip_info['lng']
            city, state = zip_info.get('city', ''), zip_info.get('state', '')
            
            print(f"Using coordinates for {zip_code} ({city}, {state}): {lat}, {lng}")
            
            # Use the main find_donation_opportunities method 
            places = self.finder.find_donation_opportunities(
                latitude=lat,
                longitude=lng,
                radius=radius,
                keywords=keywords,
                min_rating=0.0,
                sort_by_distance=True
            )
            
            return places[:max_results]
        else:
            print(f"No coordinates found for {zip_code}, using text search fallback")
            # Fallback to text search using coordinate-based search with default location
            # Use Seattle coordinates as fallback
            fallback_lat, fallback_lng = 47.6062, -122.3321
            
            enhanced_keywords = []
            for keyword in keywords:
                enhanced_keywords.extend([
                    f"{keyword} in {zip_code}",
                    f"{keyword} near {zip_code}",
                    f"{keyword} {zip_code}"
                ])
            
            places = self.finder.find_donation_opportunities(
                latitude=fallback_lat,
                longitude=fallback_lng,
                radius=radius * 2,  # Larger radius for text search
                keywords=enhanced_keywords[:6],  # Limit to prevent too many API calls
                min_rating=0.0,
                sort_by_distance=False
            )
            
            return places[:max_results]
        
        return []
    
    def search_by_zip_batch(self, zip_codes, keywords, max_results_per_zip=10, radius=5000):
        """Search multiple zip codes in batch"""
        all_results = {}
        
        for zip_code in zip_codes:
            print(f"\n{'='*50}")
            print(f"Processing zip code: {zip_code}")
            print(f"{'='*50}")
            
            results = self.search_by_zip(zip_code, keywords, max_results_per_zip, radius)
            all_results[zip_code] = results
            
            if results:
                print(f"Found {len(results)} donation opportunities in {zip_code}")
            else:
                print(f"No donation opportunities found in {zip_code}")
        
        return all_results