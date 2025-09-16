"""
Angle Changer for forcing content diversity when similar keywords are detected.
Implements angle variation across price segments, use cases, brands, regions, and installation scenarios.
"""

import random
from typing import List, Dict, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
import logging

class AngleType(Enum):
    """Content angle types for diversification"""
    PRICE_SEGMENT = "price_segment"
    USE_CASE = "use_case"  
    BRAND_FOCUS = "brand_focus"
    REGIONAL = "regional"
    INSTALLATION = "installation"
    COMPARISON = "comparison"
    SEASONAL = "seasonal"
    USER_TYPE = "user_type"

@dataclass
class AngleVariation:
    """Represents a content angle variation"""
    angle_type: AngleType
    modifier: str
    description: str
    keyword_prefix: str = ""
    keyword_suffix: str = ""

class AngleChanger:
    """
    Generates content angle variations to ensure diversity when similar topics are detected.
    Uses multiple dimensions of variation to create unique content perspectives.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Define angle variations for each type
        self.angle_variations = {
            AngleType.PRICE_SEGMENT: [
                AngleVariation(AngleType.PRICE_SEGMENT, "budget", "Budget-friendly options under $50", "cheap ", ""),
                AngleVariation(AngleType.PRICE_SEGMENT, "mid_range", "Mid-range options $50-$150", "", " under 150"),
                AngleVariation(AngleType.PRICE_SEGMENT, "premium", "Premium options over $150", "premium ", ""),
                AngleVariation(AngleType.PRICE_SEGMENT, "value", "Best value for money options", "best value ", ""),
                AngleVariation(AngleType.PRICE_SEGMENT, "luxury", "High-end luxury options", "luxury ", ""),
            ],
            
            AngleType.USE_CASE: [
                AngleVariation(AngleType.USE_CASE, "apartment", "Perfect for apartment living", "", " for apartments"),
                AngleVariation(AngleType.USE_CASE, "family", "Family-friendly solutions", "", " for families"),
                AngleVariation(AngleType.USE_CASE, "elderly", "Senior-friendly easy setup", "", " for seniors"),
                AngleVariation(AngleType.USE_CASE, "tech_enthusiast", "Advanced features for tech lovers", "advanced ", ""),
                AngleVariation(AngleType.USE_CASE, "pet_owners", "Solutions for pet owners", "", " for pet owners"),
                AngleVariation(AngleType.USE_CASE, "energy_saving", "Energy efficiency focused", "energy efficient ", ""),
                AngleVariation(AngleType.USE_CASE, "security", "Security-focused applications", "security ", ""),
                AngleVariation(AngleType.USE_CASE, "convenience", "Maximum convenience features", "", " with convenience"),
            ],
            
            AngleType.BRAND_FOCUS: [
                AngleVariation(AngleType.BRAND_FOCUS, "amazon", "Amazon ecosystem integration", "amazon ", ""),
                AngleVariation(AngleType.BRAND_FOCUS, "google", "Google Assistant compatible", "google ", ""),
                AngleVariation(AngleType.BRAND_FOCUS, "apple", "Apple HomeKit integration", "apple homekit ", ""),
                AngleVariation(AngleType.BRAND_FOCUS, "generic", "Brand-agnostic universal solutions", "universal ", ""),
                AngleVariation(AngleType.BRAND_FOCUS, "multi_brand", "Multi-platform compatibility", "compatible ", ""),
            ],
            
            AngleType.REGIONAL: [
                AngleVariation(AngleType.REGIONAL, "us", "US market availability and pricing", "", " usa"),
                AngleVariation(AngleType.REGIONAL, "uk", "UK specific models and pricing", "", " uk"),
                AngleVariation(AngleType.REGIONAL, "canada", "Canadian market options", "", " canada"),
                AngleVariation(AngleType.REGIONAL, "australia", "Australian compatibility", "", " australia"),
                AngleVariation(AngleType.REGIONAL, "international", "International shipping options", "international ", ""),
            ],
            
            AngleType.INSTALLATION: [
                AngleVariation(AngleType.INSTALLATION, "diy", "Easy DIY installation guide", "diy ", ""),
                AngleVariation(AngleType.INSTALLATION, "professional", "Professional installation required", "", " professional install"),
                AngleVariation(AngleType.INSTALLATION, "no_tools", "No tools required setup", "easy setup ", ""),
                AngleVariation(AngleType.INSTALLATION, "advanced", "Advanced installation features", "", " advanced setup"),
                AngleVariation(AngleType.INSTALLATION, "rental", "Rental-friendly removable options", "rental friendly ", ""),
            ],
            
            AngleType.COMPARISON: [
                AngleVariation(AngleType.COMPARISON, "vs_alternatives", "Compared to alternatives", "", " vs alternatives"),
                AngleVariation(AngleType.COMPARISON, "pros_cons", "Detailed pros and cons analysis", "", " pros and cons"),
                AngleVariation(AngleType.COMPARISON, "before_after", "Before and after comparison", "", " before after"),
                AngleVariation(AngleType.COMPARISON, "upgrade", "Upgrade comparison guide", "", " upgrade guide"),
            ],
            
            AngleType.SEASONAL: [
                AngleVariation(AngleType.SEASONAL, "winter", "Winter-specific considerations", "winter ", ""),
                AngleVariation(AngleType.SEASONAL, "summer", "Summer usage and benefits", "summer ", ""),
                AngleVariation(AngleType.SEASONAL, "holiday", "Holiday season recommendations", "holiday ", ""),
                AngleVariation(AngleType.SEASONAL, "back_to_school", "Back-to-school setup", "", " back to school"),
                AngleVariation(AngleType.SEASONAL, "spring_cleaning", "Spring cleaning and organization", "spring ", ""),
            ],
            
            AngleType.USER_TYPE: [
                AngleVariation(AngleType.USER_TYPE, "beginner", "Beginner-friendly guides", "beginner ", ""),
                AngleVariation(AngleType.USER_TYPE, "expert", "Expert-level analysis", "expert ", ""),
                AngleVariation(AngleType.USER_TYPE, "busy_professional", "For busy professionals", "", " for professionals"),
                AngleVariation(AngleType.USER_TYPE, "student", "Student budget solutions", "student ", ""),
                AngleVariation(AngleType.USER_TYPE, "homeowner", "Homeowner long-term solutions", "", " for homeowners"),
                AngleVariation(AngleType.USER_TYPE, "renter", "Renter-friendly options", "renter ", ""),
            ]
        }
    
    def generate_angle_variations(self, base_keyword: str, 
                                 exclude_angles: List[str] = None,
                                 min_variations: int = 3) -> List[Dict]:
        """
        Generate multiple angle variations for a base keyword.
        
        Args:
            base_keyword: Original keyword to vary
            exclude_angles: List of angle types to exclude
            min_variations: Minimum number of variations to generate
            
        Returns:
            List of angle variation dictionaries
        """
        exclude_angles = exclude_angles or []
        variations = []
        
        # Get available angle types (excluding specified ones)
        available_types = [t for t in AngleType if t.value not in exclude_angles]
        
        # Shuffle for randomness
        random.shuffle(available_types)
        
        for angle_type in available_types:
            if len(variations) >= min_variations * 2:  # Generate extra for selection
                break
                
            type_variations = self.angle_variations[angle_type]
            
            # Select a random variation from this type
            variation = random.choice(type_variations)
            
            # Generate new keyword with variation
            new_keyword = self._apply_variation(base_keyword, variation)
            
            variations.append({
                'original_keyword': base_keyword,
                'new_keyword': new_keyword,
                'angle_type': angle_type.value,
                'modifier': variation.modifier,
                'description': variation.description,
                'reason': f"Applied {angle_type.value} angle: {variation.modifier}"
            })
        
        # Return requested number of variations
        return variations[:min_variations] if len(variations) >= min_variations else variations
    
    def _apply_variation(self, keyword: str, variation: AngleVariation) -> str:
        """
        Apply angle variation to a keyword.
        
        Args:
            keyword: Base keyword
            variation: Angle variation to apply
            
        Returns:
            Modified keyword
        """
        new_keyword = keyword.strip()
        
        # Apply prefix
        if variation.keyword_prefix:
            new_keyword = variation.keyword_prefix + new_keyword
        
        # Apply suffix
        if variation.keyword_suffix:
            new_keyword = new_keyword + variation.keyword_suffix
        
        # Clean up spacing
        new_keyword = ' '.join(new_keyword.split())
        
        return new_keyword
    
    def force_angle_change(self, base_keyword: str, recent_angles: List[str] = None,
                          preferred_types: List[AngleType] = None) -> Dict:
        """
        Force an angle change for a keyword that's too similar to recent content.
        
        Args:
            base_keyword: Original keyword
            recent_angles: List of recently used angle types to avoid
            preferred_types: Preferred angle types to try first
            
        Returns:
            Dictionary with new keyword and angle information
        """
        recent_angles = recent_angles or []
        
        # Start with preferred types if specified
        candidate_types = list(preferred_types) if preferred_types else []
        
        # Add remaining types
        all_types = [t for t in AngleType if t not in candidate_types]
        candidate_types.extend(all_types)
        
        # Filter out recently used angles
        available_types = [t for t in candidate_types if t.value not in recent_angles]
        
        if not available_types:
            # If all angles were recently used, use any angle but log warning
            available_types = list(AngleType)
            self.logger.warning(f"All angle types recently used for keyword: {base_keyword}")
        
        # Select first available type
        selected_type = available_types[0]
        
        # Get a random variation of this type
        type_variations = self.angle_variations[selected_type]
        selected_variation = random.choice(type_variations)
        
        # Apply the variation
        new_keyword = self._apply_variation(base_keyword, selected_variation)
        
        result = {
            'original_keyword': base_keyword,
            'new_keyword': new_keyword,
            'angle_type': selected_type.value,
            'modifier': selected_variation.modifier,
            'description': selected_variation.description,
            'reason': f"Forced angle change to avoid similarity: {selected_type.value}",
            'novelty_penalty': 0.2  # Penalty for forced change
        }
        
        self.logger.info(f"Forced angle change: '{base_keyword}' -> '{new_keyword}' "
                        f"(angle: {selected_type.value})")
        
        return result
    
    def suggest_complementary_angles(self, base_keyword: str, 
                                   current_angle: str) -> List[Dict]:
        """
        Suggest complementary angles for content series planning.
        
        Args:
            base_keyword: Base keyword
            current_angle: Current angle being used
            
        Returns:
            List of complementary angle suggestions
        """
        complementary_map = {
            'price_segment': [AngleType.USE_CASE, AngleType.COMPARISON],
            'use_case': [AngleType.PRICE_SEGMENT, AngleType.INSTALLATION],
            'brand_focus': [AngleType.COMPARISON, AngleType.USE_CASE],
            'installation': [AngleType.USER_TYPE, AngleType.USE_CASE],
            'comparison': [AngleType.PRICE_SEGMENT, AngleType.USE_CASE],
            'seasonal': [AngleType.USE_CASE, AngleType.PRICE_SEGMENT],
            'user_type': [AngleType.INSTALLATION, AngleType.PRICE_SEGMENT]
        }
        
        complementary_types = complementary_map.get(current_angle, [AngleType.USE_CASE])
        
        suggestions = []
        for angle_type in complementary_types:
            variations = self.generate_angle_variations(base_keyword, [current_angle], 1)
            if variations:
                suggestions.extend(variations)
        
        return suggestions
    
    def get_angle_statistics(self) -> Dict:
        """Get statistics about available angle variations"""
        stats = {}
        
        for angle_type, variations in self.angle_variations.items():
            stats[angle_type.value] = {
                'total_variations': len(variations),
                'modifiers': [v.modifier for v in variations]
            }
        
        stats['total_angle_types'] = len(self.angle_variations)
        stats['total_variations'] = sum(len(variations) for variations in self.angle_variations.values())
        
        return stats

# Example usage and testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test angle changer
    changer = AngleChanger()
    
    # Test angle variations
    base_keyword = "smart plug alexa"
    variations = changer.generate_angle_variations(base_keyword, min_variations=5)
    
    print(f"Base keyword: {base_keyword}")
    print("Generated variations:")
    for i, var in enumerate(variations, 1):
        print(f"{i}. {var['new_keyword']} ({var['angle_type']}: {var['modifier']})")
        print(f"   Reason: {var['reason']}")
        print()
    
    # Test forced angle change
    forced_change = changer.force_angle_change(base_keyword, ['price_segment', 'use_case'])
    print(f"Forced change: {forced_change}")
    
    # Get statistics
    stats = changer.get_angle_statistics()
    print(f"\\nAngle statistics: {stats['total_angle_types']} types, "
          f"{stats['total_variations']} total variations")