import unittest

from lead_ingest.shopify_security import (
    ShopifyContext,
    calculate_hmac,
    canonical_message,
    context_from_params,
    sign_context,
    verify_context_token,
    verify_hmac,
)


class ShopifySecurityTests(unittest.TestCase):
    def setUp(self):
        self.secret = "test-secret"
        self.params = {
            "shop": "bentondrones.myshopify.com",
            "logged_in_customer_id": "12345",
            "page_url": "/pages/drone-delivery",
            "timestamp": "1234567890",
        }

    def test_canonical_message_sorts_and_excludes_signatures(self):
        params = {**self.params, "hmac": "ignored", "signature": "ignored"}
        message = canonical_message(params)
        self.assertNotIn("hmac", message)
        self.assertNotIn("signature", message)
        self.assertTrue(message.startswith("logged_in_customer_id=12345"))

    def test_valid_hmac_passes(self):
        signed = {**self.params}
        signed["hmac"] = calculate_hmac(signed, self.secret)
        self.assertTrue(verify_hmac(signed, self.secret))

    def test_invalid_hmac_fails(self):
        signed = {**self.params, "hmac": "bad"}
        self.assertFalse(verify_hmac(signed, self.secret))

    def test_missing_secret_fails(self):
        signed = {**self.params, "hmac": calculate_hmac(self.params, self.secret)}
        self.assertFalse(verify_hmac(signed, ""))

    def test_context_from_params_maps_shopify_values(self):
        context = context_from_params(self.params)
        self.assertEqual(context.shop, "bentondrones.myshopify.com")
        self.assertEqual(context.logged_in_customer_id, "12345")
        self.assertEqual(context.page_url, "/pages/drone-delivery")

    def test_context_token_round_trip(self):
        context = ShopifyContext(
            shop="bentondrones.myshopify.com",
            logged_in_customer_id="12345",
            page_url="/pages/drone-delivery",
        )
        token = sign_context(context, self.secret)
        verified = verify_context_token(token, self.secret)
        self.assertEqual(verified, context)

    def test_tampered_context_token_fails(self):
        context = ShopifyContext(shop="bentondrones.myshopify.com")
        token = sign_context(context, self.secret)
        tampered = token.replace(".", "x.", 1)
        self.assertIsNone(verify_context_token(tampered, self.secret))

    def test_verify_hmac_no_signature_field_returns_false(self):
        params = {"shop": "test.myshopify.com"}
        self.assertFalse(verify_hmac(params, self.secret))

    def test_verify_hmac_empty_params_returns_false(self):
        self.assertFalse(verify_hmac({}, self.secret))

    def test_verify_hmac_with_signature_field(self):
        """The 'signature' field is also accepted as an alternative to 'hmac'."""
        signed = {**self.params}
        signed["signature"] = calculate_hmac(signed, self.secret)
        self.assertTrue(verify_hmac(signed, self.secret))

    def test_verify_context_token_empty_token_returns_none(self):
        self.assertIsNone(verify_context_token("", self.secret))

    def test_verify_context_token_empty_secret_returns_none(self):
        context = ShopifyContext(shop="test.myshopify.com")
        token = sign_context(context, self.secret)
        self.assertIsNone(verify_context_token(token, ""))

    def test_verify_context_token_no_dot_returns_none(self):
        self.assertIsNone(verify_context_token("nodothere", self.secret))

    def test_verify_context_token_wrong_secret_returns_none(self):
        context = ShopifyContext(shop="test.myshopify.com")
        token = sign_context(context, self.secret)
        self.assertIsNone(verify_context_token(token, "wrong-secret"))

    def test_context_as_form_fields_maps_correctly(self):
        context = ShopifyContext(
            shop="bentondrones.myshopify.com",
            logged_in_customer_id="67890",
            page_url="/pages/test",
        )
        fields = context.as_form_fields()
        self.assertEqual(fields["shopify_shop_domain"], "bentondrones.myshopify.com")
        self.assertEqual(fields["shopify_customer_id"], "67890")
        self.assertEqual(fields["shopify_page_url"], "/pages/test")

    def test_context_from_params_with_missing_keys(self):
        context = context_from_params({})
        self.assertEqual(context.shop, "")
        self.assertEqual(context.logged_in_customer_id, "")
        self.assertEqual(context.page_url, "")

    def test_sign_context_with_empty_secret(self):
        """sign_context should still produce a token even with empty secret
        (verification will fail, but signing should not crash)."""
        context = ShopifyContext(shop="test.myshopify.com")
        token = sign_context(context, "")
        self.assertIn(".", token)
        # Verification with empty secret should fail.
        self.assertIsNone(verify_context_token(token, ""))

    def test_first_values_normalizes_list_values(self):
        from lead_ingest.shopify_security import first_values
        result = first_values({"a": ["1"], "b": "2"})
        self.assertEqual(result, {"a": "1", "b": "2"})

    def test_parse_query_returns_first_values(self):
        from lead_ingest.shopify_security import parse_query
        result = parse_query("shop=test.myshopify.com&page_url=/pages/x")
        self.assertEqual(result["shop"], "test.myshopify.com")
        self.assertEqual(result["page_url"], "/pages/x")

    def test_parse_query_handles_blank_values(self):
        from lead_ingest.shopify_security import parse_query
        result = parse_query("shop=&page_url=/pages/x")
        self.assertIn("shop", result)
        self.assertEqual(result["shop"], "")

    def test_calculate_hmac_is_deterministic(self):
        sig1 = calculate_hmac(self.params, self.secret)
        sig2 = calculate_hmac(self.params, self.secret)
        self.assertEqual(sig1, sig2)

    def test_calculate_hmac_different_secret_different_result(self):
        sig1 = calculate_hmac(self.params, self.secret)
        sig2 = calculate_hmac(self.params, "other-secret")
        self.assertNotEqual(sig1, sig2)


if __name__ == "__main__":
    unittest.main()
