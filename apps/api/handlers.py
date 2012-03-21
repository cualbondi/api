from apps.core.models import Ciudad, Linea, Recorrido
from piston.handler import BaseHandler
from piston.utils import rc
from django.core.exceptions import ObjectDoesNotExist
from settings import RADIO_ORIGEN_DEFAULT, RADIO_DESTINO_DEFAULT, CACHE_TIMEOUT, LONGITUD_PAGINA, USE_CACHE
from django.contrib.gis.geos import Point
from django.core.cache import cache
from hashlib import sha1


class CiudadHandler(BaseHandler):
    allowed_methods = ['GET']
    model = Ciudad
    exclude = ()

    def read(self, request, id_ciudad=None):
        if id_ciudad is None:
            return Ciudad.objects.all()
        else:
            try:
                return Ciudad.objects.get(id=id_ciudad)
            except ObjectDoesNotExist:
                return rc.NOT_FOUND


class CiudadLineaHandler(BaseHandler):
    allowed_methods = ['GET']
    exclude = ()

    def read(self, request, id_ciudad=None):
        if id_ciudad is None:
            return rc.BAD_REQUEST
        else:
            try:
                return Ciudad.objects.get(id=id_ciudad).lineas.all()
            except ObjectDoesNotExist:
                return rc.NOT_FOUND


class CiudadRecorridoHandler(BaseHandler):
    allowed_methods = ['GET']
    exclude = ()

    def read(self, request, id_ciudad=None):
        if id_ciudad is None:
            return rc.BAD_REQUEST
        else:
            try:
                return Ciudad.objects.get(id=id_ciudad).recorridos.all()
            except ObjectDoesNotExist:
                return rc.NOT_FOUND


class LineaHandler(BaseHandler):
    allowed_methods = ['GET']
    model = Linea
    exclude = ()

    def read(self, request, id_linea=None):
        if id_linea is None:
            # Devolver la lista completa de Lineas
            return Linea.objects.all()
        else:
            try:
                return Linea.objects.get(id=id_linea)
            except ObjectDoesNotExist:
                return rc.NOT_FOUND


class LineaRecorridoHandler(BaseHandler):
    allowed_methods = ['GET']
    exclude = ()

    def read(self, request, id_linea=None):
        if id_linea is None:
            return rc.BAD_REQUEST
        else:
            try:
                l = Linea.objects.get(id=id_linea)
                return Recorrido.objects.filter(linea=l)
            except ObjectDoesNotExist:
                return rc.NOT_FOUND


class RecorridoHandler(BaseHandler):
    allowed_methods = ['GET']
    model = Recorrido
    exclude = ()

    def _get_response_from_cache(self, origen, destino, radio_origen, radio_destino, combinar):
        concat = str(origen) + str(destino) + str(radio_origen) + str(radio_destino) + str(combinar)
        key = sha1(concat).hexdigest()
        response = cache.get(key)
        if not response:
            # No se encontro la response en la cache
            return None
        return response

    def _save_in_cache(self, origen, destino, radio_origen, radio_destino, combinar, recorridos):
        concat = str(origen) + str(destino) + str(radio_origen) + str(radio_destino) + str(combinar)
        key = sha1(concat).hexdigest()
        cache.set(key, recorridos, CACHE_TIMEOUT)

    def _paginar(self, recorridos, pagina):
        desde = (pagina-1)*LONGITUD_PAGINA
        hasta = desde+LONGITUD_PAGINA
        return recorridos[desde:hasta]

    def read(self, request, id_recorrido=None):
        if id_recorrido is None:
            origen = request.GET.get('origen', None)
            destino = request.GET.get('destino', None)
            radio_origen = request.GET.get('radio_origen', RADIO_ORIGEN_DEFAULT)
            radio_destino = request.GET.get('radio_destino', RADIO_DESTINO_DEFAULT)
            query = request.GET.get('query', None)

            combinar = request.GET.get('combinar', 'false')
            if combinar == 'true': combinar = True
            elif combinar == 'false': combinar = False
            else: return rc.BAD_REQUEST

            pagina = request.GET.get('pagina', None)
            if pagina is not None:
                try:
                    pagina = int(pagina)
                except ValueError:
                    return rc.BAD_REQUEST

            if query is not None:
                # Buscar recorridos por nombre
                rc.NOT_IMPLEMENTED
            elif origen is not None and destino is not None:
                # Buscar geograficamente en base a origen y destino
                origen = str(origen).split(",")
                try:
                    latitud_origen = float(origen[1])
                    longitud_origen = float(origen[0])
                except ValueError:
                    return rc.BAD_REQUEST
                origen = Point(longitud_origen, latitud_origen)

                destino = str(destino).split(",")
                try:
                    latitud_destino = float(destino[1])
                    longitud_destino = float(destino[0])
                except ValueError:
                    return rc.BAD_REQUEST
                destino = Point(longitud_destino, latitud_destino)

                if USE_CACHE:
                    recorridos = self._get_response_from_cache(origen, destino,
                                    radio_origen, radio_destino, combinar)
                else: recorridos = None

                if recorridos is None:
                    # No se encontro en la cache, hay que buscarlo en la DB.
                    if not combinar:
                        # Buscar SIN transbordo
                        recorridos = Recorrido.objects.get_recorridos(origen, destino, radio_origen, radio_destino)
                    else:
                        # Buscar CON transbordo
                        recorridos = Recorrido.objects.get_recorridos_combinados(origen, destino, radio_origen, radio_destino)
                        return rc.NOT_IMPLEMENTED
                    # Guardar los resultados calculados en memcached
                    if USE_CACHE:
                        self._save_in_cache(origen, destino, radio_origen, radio_destino, combinar, recorridos)
                if pagina is not None:
                    # Filtrar todos los recorridos y devolver solo la pagina pedida
                    recorridos = self._paginar(recorridos, pagina)
                return recorridos
            else:
                # Sin parametros GET, devolver todos los recorridos
                return Recorrido.objects.all()
        else:
            # Me mandaron "id_recorrido", tengo que devolver ese solo recorrido.
            try:
                return Recorrido.objects.get(id=id_recorrido)
            except ObjectDoesNotExist:
                return rc.NOT_FOUND



