#!/usr/bin/env python3
"""
Command-line interface for the Donation Opportunities Finder

This script provides a simple CLI for finding donation opportunities
using zip codes or coordinates.
"""

import argparse
import sys
import json
import os
from donation_finder import DonationFinderNew
from zip_finder import SimpleZipCodeFinder
from email_sender import EmailSender


def load_config():
    """Load configuration from config.json"""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("Warning: config.json is not valid JSON. Using defaults.")
        return {}


def get_api_key():
    """Get API key from environment, .env file, or .env.example"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    
    api_key = os.getenv('GOOGLE_PLACES_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
    
    # If not found, try to read from .env.example
    if not api_key:
        try:
            with open('.env.example', 'r') as f:
                for line in f:
                    if 'API_KEY=' in line and not line.strip().startswith('#'):
                        api_key = line.split('=', 1)[1].strip()
                        break
        except FileNotFoundError:
            pass
    
    if not api_key:
        print("Error: Google Places API key not found.")
        print("Please set GOOGLE_PLACES_API_KEY or GOOGLE_MAPS_API_KEY in environment, .env file, or .env.example")
        sys.exit(1)
    
    return api_key


def save_results(places, filename_base, format='both'):
    """Save results to file(s) in specified format(s)"""
    if not places:
        print("No results to save.")
        return []
    
    saved_files = []
    
    if format in ['json', 'both']:
        json_file = f"{filename_base}.json"
        with open(json_file, 'w') as f:
            json.dump(places, f, indent=2)
        print(f"Results saved to {json_file}")
        saved_files.append(json_file)
    
    if format in ['csv', 'both']:
        import csv
        csv_file = f"{filename_base}.csv"
        
        # Get all possible fieldnames
        fieldnames = set()
        for place in places:
            fieldnames.update(place.keys())
        fieldnames = sorted(fieldnames)
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(places)
        print(f"Results saved to {csv_file}")
        saved_files.append(csv_file)
    
    return saved_files


def send_email_results(places, search_info, attach_files=None):
    """Send results via email if configured"""
    try:
        email_sender = EmailSender()
        
        if not email_sender.is_configured():
            print("📧 Email not configured - skipping email delivery")
            return False
        
        return email_sender.send_results_email(places, search_info, attach_files)
    
    except Exception as e:
        print(f"📧 Email sending failed: {e}")
        return False


def print_results(places, quiet=False, show_reviews=False):
    """Print results to console"""
    if not places:
        print("No donation opportunities found.")
        return
    
    print(f"\nFound {len(places)} donation opportunities:")
    print("-" * 80)
    
    for i, place in enumerate(places, 1):
        if quiet:
            # Compact format
            distance = f" ({place['distance_km']:.1f}km)" if 'distance_km' in place else ""
            rating = f" ⭐{place['rating']}" if place.get('rating') else ""
            review_count = f" ({place.get('user_ratings_total', 0)} reviews)" if place.get('user_ratings_total') else ""
            print(f"{i}. {place['name']}{distance}{rating}{review_count}")
        else:
            # Detailed format
            print(f"{i}. {place['name']}")
            if 'formatted_address' in place:
                print(f"   📍 {place['formatted_address']}")
            if 'rating' in place and place['rating'] is not None:
                total_reviews = place.get('user_ratings_total', 0)
                review_text = f" ({total_reviews} reviews)" if total_reviews > 0 else ""
                print(f"   ⭐ Rating: {place['rating']}/5{review_text}")
            if 'distance_km' in place:
                print(f"   📏 Distance: {place['distance_km']:.1f} km")
            if place.get('phone'):
                print(f"   📞 Phone: {place['phone']}")
            if place.get('website'):
                print(f"   🌐 Website: {place['website']}")
            if place.get('email'):
                print(f"   📧 Email: {place['email']}")
            if place.get('opening_hours'):
                print(f"   🕒 Hours: {place['opening_hours'][0]}")
            if 'types' in place:
                print(f"   🏷️  Categories: {', '.join(place['types'][:3])}")
            
            # Show reviews if available and requested
            if show_reviews and place.get('reviews'):
                print(f"   📝 Reviews ({len(place['reviews'])}):")
                for review in place['reviews']:
                    author = review.get('author_name', 'Anonymous')
                    rating = "⭐" * review.get('rating', 0)
                    time_desc = review.get('time_description', '')
                    text = review.get('text', '')[:200] + "..." if len(review.get('text', '')) > 200 else review.get('text', '')
                    print(f"      • {author} {rating} {time_desc}")
                    if text.strip():
                        print(f"        \"{text}\"")
            print()


def main():
    parser = argparse.ArgumentParser(
        description='Find donation opportunities using Google Maps Places API'
    )
    
    # Location options
    location_group = parser.add_mutually_exclusive_group(required=True)
    location_group.add_argument('--zip', type=str, help='Search by ZIP code')
    location_group.add_argument('--zip-batch', action='store_true', 
                              help='Search multiple ZIP codes from config')
    location_group.add_argument('--lat', type=float, help='Latitude for coordinate search')
    
    # Coordinate search requires both lat and lng
    parser.add_argument('--lng', type=float, help='Longitude for coordinate search')
    
    # Search parameters
    parser.add_argument('--keywords', type=str, 
                       default='food bank,charity,shelter,blood bank',
                       help='Comma-separated keywords (default: food bank,charity,shelter,blood bank)')
    parser.add_argument('--radius', type=int, default=5000,
                       help='Search radius in meters (default: 5000)')
    parser.add_argument('--max-results', type=int, default=20,
                       help='Maximum results to return (default: 20)')
    
    # Reviews feature
    parser.add_argument('--include-reviews', action='store_true',
                       help='Fetch user reviews for each place (slower but more detailed)')
    parser.add_argument('--max-reviews', type=int, default=3,
                       help='Maximum reviews per place when --include-reviews is used (default: 3)')
    parser.add_argument('--reviews-for-all', action='store_true',
                       help='Get reviews for all places, not just highly rated ones')
    
    # Output options
    parser.add_argument('--output', type=str, default='donation_opportunities',
                       help='Output filename base (without extension)')
    parser.add_argument('--format', choices=['json', 'csv', 'both'], default='both',
                       help='Output format (default: both)')
    parser.add_argument('--email', action='store_true',
                       help='Send results via email to configured recipient')
    parser.add_argument('--quiet', action='store_true',
                       help='Quiet mode - compact output')
    
    args = parser.parse_args()
    
    # Validate coordinate search
    if args.lat is not None and args.lng is None:
        parser.error("--lng is required when using --lat")
    if args.lng is not None and args.lat is None:
        parser.error("--lat is required when using --lng")
    
    # Get API key
    api_key = get_api_key()
    
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',')]
    
    try:
        if args.zip:
            # Single ZIP code search
            print(f"🔍 Searching for donation opportunities in ZIP code: {args.zip}")
            print(f"🔑 Keywords: {', '.join(keywords)}")
            print(f"📏 Radius: {args.radius}m")
            print()
            
            finder = SimpleZipCodeFinder(api_key)
            places = finder.search_by_zip(args.zip, keywords, args.max_results, args.radius)
            
            # Enhance with reviews if requested
            if places and args.include_reviews:
                print(f"\n🔍 Fetching detailed reviews for {len(places)} places...")
                donation_finder = DonationFinderNew(api_key)
                places = donation_finder.enhance_places_with_reviews(
                    places, 
                    max_reviews=args.max_reviews,
                    include_all=args.reviews_for_all
                )
                # Show API usage statistics
                print(f"\n📊 API Usage Summary: {donation_finder.total_api_calls} total Google Places API calls made")
            
            if places:
                print_results(places, args.quiet, args.include_reviews)
                saved_files = save_results(places, f"{args.output}_{args.zip}", args.format)
                
                # Send email if requested
                if args.email:
                    search_info = {
                        'type': f'ZIP Code Search',
                        'location': f'ZIP {args.zip}',
                        'keywords': ', '.join(keywords)
                    }
                    send_email_results(places, search_info, saved_files)
            
        elif args.zip_batch:
            # Multiple ZIP codes from config
            config = load_config()
            zip_codes = config.get('zip_codes', {}).get('enabled_zip_codes', [])
            
            if not zip_codes:
                print("No ZIP codes found in config.json")
                sys.exit(1)
            
            print(f"🔍 Batch searching {len(zip_codes)} ZIP codes: {', '.join(zip_codes)}")
            print(f"🔑 Keywords: {', '.join(keywords)}")
            print()
            
            finder = SimpleZipCodeFinder(api_key)
            all_results = finder.search_by_zip_batch(
                zip_codes, keywords, args.max_results//len(zip_codes), args.radius
            )
            
            # Combine all results
            all_places = []
            for zip_code, places in all_results.items():
                all_places.extend(places)
            
            # Enhance with reviews if requested
            if all_places and args.include_reviews:
                print(f"\n🔍 Fetching detailed reviews for {len(all_places)} places from batch search...")
                donation_finder = DonationFinderNew(api_key)
                all_places = donation_finder.enhance_places_with_reviews(
                    all_places, 
                    max_reviews=args.max_reviews,
                    include_all=args.reviews_for_all
                )
                # Show API usage statistics
                print(f"\n📊 API Usage Summary: {donation_finder.total_api_calls} total Google Places API calls made")
            
            if all_places:
                print(f"\n🎯 Combined results from all ZIP codes:")
                print_results(all_places, args.quiet, args.include_reviews)
                saved_files = save_results(all_places, f"{args.output}_batch", args.format)
                
                # Send email if requested
                if args.email:
                    search_info = {
                        'type': 'Batch ZIP Code Search',
                        'location': f'{len(zip_codes)} ZIP codes: {", ".join(zip_codes)}',
                        'keywords': ', '.join(keywords)
                    }
                    send_email_results(all_places, search_info, saved_files)
            
            # Save individual results too (without reviews enhancement for individual files)
            for zip_code, places in all_results.items():
                if places:
                    save_results(places, f"{args.output}_{zip_code}", args.format)
                    
        else:
            # Coordinate search
            print(f"🔍 Searching for donation opportunities at coordinates: {args.lat}, {args.lng}")
            print(f"🔑 Keywords: {', '.join(keywords)}")
            print(f"📏 Radius: {args.radius}m")
            print()
            
            finder = DonationFinderNew(api_key)
            
            all_places = []
            for keyword in keywords:
                enhanced_keyword = f"{keyword} near me"
                print(f"Searching: '{enhanced_keyword}'")
                places = finder.search_places(
                    args.lat, args.lng, args.radius, enhanced_keyword, min_rating=0.0
                )
                if places:
                    all_places.extend(places)
            
            if all_places:
                unique_places = finder.deduplicate_places(all_places)
                processed_places = finder.process_places(unique_places, args.lat, args.lng)
                final_places = processed_places[:args.max_results]
                
                # Enhance with reviews if requested
                if args.include_reviews:
                    print(f"\n🔍 Fetching detailed reviews for {len(final_places)} places...")
                    final_places = finder.enhance_places_with_reviews(
                        final_places, 
                        max_reviews=args.max_reviews,
                        include_all=args.reviews_for_all
                    )
                    # Show API usage statistics
                    print(f"\n📊 API Usage Summary: {finder.total_api_calls} total Google Places API calls made")
                
                print_results(final_places, args.quiet, args.include_reviews)
                saved_files = save_results(final_places, f"{args.output}_coordinates", args.format)
                
                # Send email if requested
                if args.email:
                    search_info = {
                        'type': 'Coordinates Search',
                        'location': f'Lat: {args.lat}, Lng: {args.lng}',
                        'keywords': ', '.join(keywords)
                    }
                    send_email_results(final_places, search_info, saved_files)
            else:
                print("No donation opportunities found.")
    
    except KeyboardInterrupt:
        print("\nSearch cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()