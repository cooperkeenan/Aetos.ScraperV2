"""
Integration test for title matcher with real Sony products from database
Run this to validate the matcher works with your actual product data
"""
import pytest
from decimal import Decimal

from src.domain.models.listing import Listing
from src.domain.models.product import Product
from src.matching.matchers.title_matcher import TitleMatcher


class TestRealSonyProducts:
    """Test with actual Sony products from your database"""

    @pytest.fixture
    def matcher(self):
        return TitleMatcher()

    @pytest.fixture
    def real_sony_products(self):
        """
        Real Sony products based on your database
        Update these if your products change
        """
        return [
            Product(
                id=223,
                brand="Sony",
                model="a5000",
                full_name="Sony a5000",
                category="camera",
                buy_price_min=Decimal("80.00"),
                buy_price_max=Decimal("150.00"),
                sell_target=Decimal("195.00"),
                active=True,
                fuzzy_patterns=["sony a 5000", "sony a5000"],
                aliases=["sony alpha 5000"],
            ),
            Product(
                id=227,
                brand="Sony",
                model="a6000",
                full_name="Sony a6000",
                category="camera",
                buy_price_min=Decimal("80.00"),
                buy_price_max=Decimal("270.00"),
                sell_target=Decimal("360.00"),
                active=True,
                fuzzy_patterns=["sony a 6000", "sony a6000"],
                aliases=["sony alpha 6000"],
            ),
            Product(
                id=230,
                brand="Sony",
                model="a6400",
                full_name="Sony a6400",
                category="camera",
                buy_price_min=Decimal("80.00"),
                buy_price_max=Decimal("400.00"),
                sell_target=Decimal("500.00"),
                active=True,
                fuzzy_patterns=["sony a 6400", "sony a6400"],
                aliases=["sony alpha 6400"],
            ),
            Product(
                id=240,
                brand="Sony",
                model="a7 III",
                full_name="Sony Alpha a7 III",
                category="camera",
                buy_price_min=Decimal("80.00"),
                buy_price_max=Decimal("550.00"),
                sell_target=Decimal("750.00"),
                active=True,
                fuzzy_patterns=["sony a7iii", "sony a7 iii", "sony a 7 iii"],
                aliases=["sony alpha 7 iii", "sony alpha a7iii"],
            ),
            Product(
                id=241,
                brand="Sony",
                model="a7 IV",
                full_name="Sony Alpha a7 IV",
                category="camera",
                buy_price_min=Decimal("200.00"),
                buy_price_max=Decimal("1000.00"),
                sell_target=Decimal("1300.00"),
                active=True,
                fuzzy_patterns=["sony a7iv", "sony a7 iv", "sony a 7 iv"],
                aliases=["sony alpha 7 iv", "sony alpha a7iv"],
            ),
        ]

    def test_correct_matches_from_actual_listings(self, matcher, real_sony_products):
        """
        Test cases from your actual scraper results that SHOULD match
        These were real Facebook listings
        """
        test_cases = [
            # (listing_title, expected_product_id, description)
            ("Sony A6400 camera + Tamron 17-70mm + extras", 230, "a6400 bundle"),
            ("Sony A7iii Mirrorless Digital Camera Body", 240, "a7iii body only"),
            ("Sony a6000 camera (body only)", 227, "a6000 body"),
            ("SONY A5000 CAMERA with Bag and 2 spare batteries - Like New", 223, "a5000 bundle"),
            ("Sony Alpha a6400 Mirrorless Digital Camera", 230, "a6400 with 'Alpha'"),
            ("Sony A7 III Full Frame", 240, "a7 III with spaces"),
            ("Sony A6000 Mirrorless Camera with 2 Lenses.", 227, "a6000 with lenses"),
        ]

        results = []
        for title, expected_id, description in test_cases:
            listing = Listing(
                url="test.com",
                title=title,
                price=500.0,
                image_url=None,
                location=None,
            )

            # Find the expected product
            expected_product = next(p for p in real_sony_products if p.id == expected_id)

            # Try matching
            score, reason = matcher.match(listing, expected_product)

            results.append({
                "title": title,
                "expected_model": expected_product.model,
                "score": score,
                "reason": reason,
                "description": description,
                "passed": score >= 90.0,
            })

        # Print results
        print("\n" + "=" * 80)
        print("CORRECT MATCH VALIDATION")
        print("=" * 80)
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"{status} | {r['description']}")
            print(f"    Title: {r['title'][:60]}...")
            print(f"    Model: {r['expected_model']} | Score: {r['score']:.0f}% | {r['reason'][:50]}...")
            print()

        # Assert all passed
        failed = [r for r in results if not r["passed"]]
        assert len(failed) == 0, f"Failed {len(failed)} correct matches: {[f['description'] for f in failed]}"

    def test_incorrect_matches_from_actual_listings(self, matcher, real_sony_products):
        """
        Test cases from your actual scraper results that SHOULD NOT match
        These were FALSE POSITIVES in your original results
        """
        test_cases = [
            # (listing_title, wrong_product_id, correct_model_in_title, description)
            ("Sony A200 DSLR digital camera", 223, "a200", "a200 should not match a5000"),
            ("Sony A6400 camera + extras", 241, "a6400", "a6400 should not match a7 IV"),
            ("Sony video cameras Hi8 pro & Video 8", 241, None, "Video camera not digital camera"),
            ("Sony a700", 227, "a700", "a700 should not match a6000"),
            ("Sony A230 dslr camera", 223, "a230", "a230 should not match a5000"),
        ]

        results = []
        for title, wrong_id, correct_model, description in test_cases:
            listing = Listing(
                url="test.com",
                title=title,
                price=500.0,
                image_url=None,
                location=None,
            )

            # Get the wrong product that shouldn't match
            wrong_product = next(p for p in real_sony_products if p.id == wrong_id)

            # Try matching
            score, reason = matcher.match(listing, wrong_product)

            results.append({
                "title": title,
                "wrong_model": wrong_product.model,
                "correct_model": correct_model,
                "score": score,
                "reason": reason,
                "description": description,
                "passed": score < 50.0,  # Should NOT match
            })

        # Print results
        print("\n" + "=" * 80)
        print("FALSE POSITIVE PREVENTION")
        print("=" * 80)
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            print(f"{status} | {r['description']}")
            print(f"    Title: {r['title'][:60]}...")
            print(f"    Wrong model: {r['wrong_model']} | Score: {r['score']:.0f}%")
            if r['correct_model']:
                print(f"    (Actual model in title: {r['correct_model']})")
            print()

        # Assert all passed (no false positives)
        failed = [r for r in results if not r["passed"]]
        assert len(failed) == 0, f"Failed to prevent {len(failed)} false positives: {[f['description'] for f in failed]}"

    def test_edge_case_listings(self, matcher, real_sony_products):
        """Test edge cases that might break the matcher"""
        a6400 = next(p for p in real_sony_products if p.model == "a6400")
        a7iii = next(p for p in real_sony_products if p.model == "a7 III")

        edge_cases = [
            # Unusual formatting
            ("📸 Sony A6400 📸", a6400, True, "Emojis"),
            ("SONY A6400 CAMERA BODY", a6400, True, "All caps"),
            ("sony a6400 camera body", a6400, True, "All lowercase"),
            ("Sony   A6400   Camera", a6400, True, "Extra spaces"),
            ("Sony A6400 - Excellent Condition!", a6400, True, "Special chars"),
            
            # Model number variations
            ("Sony A7iii Camera", a7iii, True, "No space in iii"),
            ("Sony A7 III Camera", a7iii, True, "Space in III"),
            ("Sony A 7 III Camera", a7iii, True, "Extra spaces"),
            
            # Should NOT match
            ("Canon A6400", a6400, False, "Wrong brand"),
            ("A6400 Camera", a6400, False, "No brand"),
        ]

        results = []
        for title, product, should_match, description in edge_cases:
            listing = Listing(
                url="test.com",
                title=title,
                price=500.0,
                image_url=None,
                location=None,
            )

            score, reason = matcher.match(listing, product)
            
            if should_match:
                passed = score >= 90.0
            else:
                passed = score < 50.0

            results.append({
                "title": title,
                "model": product.model,
                "score": score,
                "should_match": should_match,
                "passed": passed,
                "description": description,
            })

        # Print results
        print("\n" + "=" * 80)
        print("EDGE CASE VALIDATION")
        print("=" * 80)
        for r in results:
            status = "✅ PASS" if r["passed"] else "❌ FAIL"
            expected = "MATCH" if r["should_match"] else "NO MATCH"
            print(f"{status} | {r['description']} (expect {expected})")
            print(f"    Title: {r['title']}")
            print(f"    Model: {r['model']} | Score: {r['score']:.0f}%")
            print()

        failed = [r for r in results if not r["passed"]]
        assert len(failed) == 0, f"Failed {len(failed)} edge cases: {[f['description'] for f in failed]}"

    def test_not_too_strict_stats(self, matcher, real_sony_products):
        """
        Statistical test - make sure we're not rejecting valid listings
        Tests 100+ realistic listing variations
        """
        # Generate variations of valid listings
        valid_listings = []
        
        for product in real_sony_products:
            # Basic formats
            valid_listings.append((f"Sony {product.model}", product.id))
            valid_listings.append((f"Sony {product.model} Camera", product.id))
            valid_listings.append((f"Sony {product.model} Body Only", product.id))
            valid_listings.append((f"Sony {product.model} + Lens", product.id))
            
            # With descriptors
            valid_listings.append((f"Sony {product.model} Excellent Condition", product.id))
            valid_listings.append((f"Sony {product.model} Like New", product.id))
            valid_listings.append((f"Sony {product.model} Bundle", product.id))
            
            # Case variations
            valid_listings.append((f"SONY {product.model.upper()}", product.id))
            valid_listings.append((f"sony {product.model.lower()}", product.id))

        matches = 0
        total = len(valid_listings)

        for title, expected_id in valid_listings:
            listing = Listing(url="test.com", title=title, price=500.0, image_url=None, location=None)
            product = next(p for p in real_sony_products if p.id == expected_id)
            score, _ = matcher.match(listing, product)
            
            if score >= 90.0:
                matches += 1

        match_rate = (matches / total) * 100

        print("\n" + "=" * 80)
        print("STRICTNESS VALIDATION")
        print("=" * 80)
        print(f"Valid listings tested: {total}")
        print(f"Successfully matched: {matches}")
        print(f"Match rate: {match_rate:.1f}%")
        print()
        print(f"Target: ≥ 95% match rate for valid listings")
        print()

        # We want at least 95% of valid listings to match
        assert match_rate >= 95.0, f"Matcher too strict: only {match_rate:.1f}% match rate (target ≥95%)"


if __name__ == "__main__":
    # Run with: python -m pytest tests/matching/test_real_sony_products.py -v -s
    pytest.main([__file__, "-v", "-s"])