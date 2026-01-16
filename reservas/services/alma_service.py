"""
Servicio de integración con ALMA API (VERSIÓN FINAL ROBUSTA)
Maneja casos donde los campos pueden venir como string o dict
"""

import requests
import logging
from django.conf import settings
from django.core.cache import cache
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class ALMAService:
    """
    Servicio para interactuar con la API de ALMA (ExLibris)
    """
    
    def __init__(self):
        self.api_key = settings.ALMA_API_KEY
        self.base_url = settings.ALMA_API_BASE_URL
        self.timeout = settings.ALMA_API_TIMEOUT
        self.cache_timeout = settings.ALMA_CACHE_TIMEOUT
    
    @staticmethod
    def _get_field_value(field, key='value', default=''):
        """
        Extrae valor de un campo que puede ser dict o string
        
        Args:
            field: Campo que puede ser dict, string u otro
            key: Clave a buscar si es dict
            default: Valor por defecto
            
        Returns:
            str: Valor extraído
        """
        if isinstance(field, dict):
            return field.get(key, default)
        elif isinstance(field, str):
            return field
        else:
            return default
        
    def verificar_deudas_usuario(self, email_usuario):
        """
        Verifica si un usuario puede reservar salas
        
        Args:
            email_usuario (str): Email institucional del usuario
        
        Returns:
            dict: Información sobre el estado del usuario
        """
        
        # 1. Buscar en caché
        cache_key = f'alma_estado_{email_usuario}'
        resultado_cache = cache.get(cache_key)
        
        if resultado_cache is not None:
            logger.info(f"ALMA: Usando caché para {email_usuario}")
            return resultado_cache
        
        # 2. Consultar API
        logger.info(f"ALMA: Consultando API para {email_usuario}")
        
        usuario_data = self._buscar_usuario_por_email(email_usuario)
        
        if not usuario_data:
            return {
                'tiene_deudas': False,
                'usuario_activo': False,
                'tiene_bloqueos': False,
                'detalles_bloqueos': [],
                'expiry_date': None,
                'mensaje': 'Usuario no registrado en sistema de biblioteca',
                'error': 'Usuario no encontrado en ALMA'
            }
        
        # Extraer información
        user_id = usuario_data.get('user_id')
        expiry_date = usuario_data.get('expiry_date')
        usuario_activo = usuario_data.get('activo', False)
        user_blocks = usuario_data.get('user_blocks', [])
        
        # Evaluar
        tiene_bloqueos = len(user_blocks) > 0
        puede_reservar = usuario_activo and not tiene_bloqueos
        
        resultado = {
            'tiene_deudas': not puede_reservar,
            'usuario_activo': usuario_activo,
            'tiene_bloqueos': tiene_bloqueos,
            'detalles_bloqueos': user_blocks,
            'expiry_date': expiry_date,
            'mensaje': self._generar_mensaje(usuario_activo, tiene_bloqueos, user_blocks, expiry_date)
        }
        
        # Guardar en caché
        cache.set(cache_key, resultado, self.cache_timeout)
        logger.info(
            f"ALMA: {email_usuario} - "
            f"Activo: {usuario_activo}, Bloqueos: {tiene_bloqueos}"
        )
        
        return resultado
    
    def _buscar_usuario_por_email(self, email_usuario):
        """
        Busca un usuario en ALMA por su email usando q=email~
        
        Args:
            email_usuario (str): Email del usuario
            
        Returns:
            dict o None
        """
        
        url = f"{self.base_url}/almaws/v1/users"
        
        headers = {
            'Authorization': f'apikey {self.api_key}',
            'Accept': 'application/json'
        }
        
        params = {
            'q': f'email~{email_usuario}',
            'expand': 'full'
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            total_records = data.get('total_record_count', 0)
            
            if total_records == 0:
                logger.warning(f"ALMA: Usuario {email_usuario} no encontrado")
                return None
            
            users = data.get('user', [])
            if not users:
                return None
            
            user = users[0]
            user_id = user.get('primary_id')
            
            # Extraer información
            expiry_date_str = user.get('expiry_date')
            usuario_activo = self._verificar_usuario_activo(expiry_date_str)
            
            # Extraer bloqueos activos de forma robusta
            user_blocks_raw = user.get('user_block', [])
            user_blocks_activos = self._filtrar_bloqueos_activos(user_blocks_raw)
            
            logger.info(
                f"ALMA: Usuario {user_id} - "
                f"Activo: {usuario_activo}, "
                f"Bloqueos: {len(user_blocks_activos)}"
            )
            
            return {
                'user_id': user_id,
                'expiry_date': expiry_date_str,
                'activo': usuario_activo,
                'user_blocks': user_blocks_activos
            }
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else 'Unknown'
            logger.error(f"ALMA: Error HTTP {status_code} buscando {email_usuario}")
            return None
                
        except Exception as e:
            logger.error(f"ALMA: Error buscando usuario {email_usuario}: {str(e)}")
            return None
    
    def _filtrar_bloqueos_activos(self, user_blocks):
        """
        Filtra bloqueos que AÚN están vigentes según su expiry_date
        Un bloqueo está activo si su expiry_date es futura (no ha expirado aún)
        
        Args:
            user_blocks (list): Lista de user_blocks
            
        Returns:
            list: Solo bloqueos vigentes
        """
        
        if not user_blocks:
            return []
        
        activos = []
        fecha_actual = datetime.now(timezone.utc)
        
        for block in user_blocks:
            try:
                expiry_date_str = block.get('expiry_date')
                
                # Si no tiene expiry_date, verificar por block_status
                if not expiry_date_str:
                    block_status = block.get('block_status', {})
                    status_value = self._get_field_value(block_status, 'value', '')
                    
                    # Si dice ACTIVE y no tiene expiry_date, considerarlo activo
                    if status_value.upper() == 'ACTIVE':
                        activos.append(block)
                        
                        desc = block.get('block_description', {})
                        desc_text = self._get_field_value(desc, 'value', 'Sin descripción')
                        logger.info(f"ALMA: Bloqueo activo (sin expiry_date) - {desc_text}")
                else:
                    # Tiene expiry_date, verificar si aún está vigente
                    try:
                        expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00'))
                        
                        # Si la fecha de expiración es futura, el bloqueo está activo
                        if expiry_date > fecha_actual:
                            activos.append(block)
                            
                            desc = block.get('block_description', {})
                            desc_text = self._get_field_value(desc, 'value', 'Sin descripción')
                            dias_restantes = (expiry_date - fecha_actual).days
                            logger.info(
                                f"ALMA: Bloqueo vigente - {desc_text} "
                                f"(expira en {dias_restantes} días)"
                            )
                        else:
                            logger.debug(f"ALMA: Bloqueo expirado, se ignora")
                    
                    except Exception as e:
                        logger.warning(f"ALMA: Error parseando expiry_date del bloqueo: {e}")
                        # Si hay error parseando, incluirlo por precaución
                        activos.append(block)
            
            except Exception as e:
                logger.warning(f"ALMA: Error procesando bloqueo: {e}")
                continue
        
        return activos
    
    def _verificar_usuario_activo(self, expiry_date_str):
        """
        Verifica si un usuario está activo según su expiry_date
        
        Args:
            expiry_date_str (str): Fecha de expiración
            
        Returns:
            bool: True si está activo
        """
        
        if not expiry_date_str:
            logger.info("ALMA: Usuario sin expiry_date, considerado activo")
            return True
        
        try:
            # Parsear fecha
            expiry_date = datetime.fromisoformat(expiry_date_str.replace('Z', '+00:00'))
            fecha_actual = datetime.now(timezone.utc)
            
            activo = expiry_date > fecha_actual
            
            if activo:
                dias = (expiry_date - fecha_actual).days
                logger.info(f"ALMA: Usuario activo, expira en {dias} días")
            else:
                logger.warning(f"ALMA: Usuario EXPIRADO")
            
            return activo
            
        except Exception as e:
            logger.error(f"ALMA: Error parseando expiry_date: {e}")
            return True  # fail-open
    
    def _generar_mensaje(self, usuario_activo, tiene_bloqueos, bloqueos, expiry_date):
        """
        Genera mensaje amigable para el usuario
        """
        
        if not usuario_activo:
            if expiry_date:
                try:
                    fecha = datetime.fromisoformat(expiry_date.replace('Z', '+00:00'))
                    fecha_str = fecha.strftime('%d/%m/%Y')
                    return f"Tu cuenta de biblioteca expiró el {fecha_str}. Contacta al mesón de préstamos."
                except:
                    return "Tu cuenta de biblioteca está inactiva. Contacta al mesón de préstamos."
            return "Tu cuenta de biblioteca está inactiva. Contacta al mesón de préstamos."
        
        if tiene_bloqueos:
            cantidad = len(bloqueos)
            
            if cantidad == 1:
                # Extraer motivo de forma robusta
                desc = bloqueos[0].get('block_description', {})
                motivo = self._get_field_value(desc, 'value', 'No especificado')
                
                nota = bloqueos[0].get('block_note', '')
                
                mensaje = f"Tienes una sanción activa: {motivo}"
                if nota:
                    mensaje += f" ({nota})"
                return mensaje
            else:
                return f"Tienes {cantidad} sanciones activas en tu cuenta de biblioteca"
        
        return "Sin restricciones en biblioteca - Puedes reservar"
    
    def invalidar_cache_usuario(self, email_usuario):
        """
        Invalida el caché de un usuario
        """
        cache_key = f'alma_estado_{email_usuario}'
        cache.delete(cache_key)
        logger.info(f"ALMA: Caché invalidado para {email_usuario}")


# Instancia global
alma_service = ALMAService()