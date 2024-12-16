from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .forms import  LoginForm
from .models import Producto
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from .forms import CrearUsuarioForm


def crear_usuario(request):
    if request.method == "POST":
        form = CrearUsuarioForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            grupo_nombre = form.cleaned_data["grupo"]

            # Crear el usuario
            nuevo_usuario = User.objects.create_user(username=username, password=password)
            # Asignar al grupo
            grupo = Group.objects.get(name=grupo_nombre)
            grupo.user_set.add(nuevo_usuario)

            messages.success(request, f"Usuario '{username}' creado exitosamente en el grupo '{grupo_nombre}'.")
            return redirect("gestion")
        else:
            messages.error(request, "Error al crear el usuario. Por favor, verifica los datos.")
    else:
        form = CrearUsuarioForm()
    return render(request, "gestion/gestion.html", {"form": form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('gestion')
    else:
        form = LoginForm()
    return render(request, 'gestion/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def gestion_filtrada(request):
    # Lista estática de todas las categorías
    categorias = [
        "Lacteos", "Embutidos", "Rotiseria", "Limpieza", "Congelados",
        "Confites", "Panaderia", "Snacks", "Dulces", "Bebidas", "Jugos"
    ]

    # Obtener la categoría seleccionada del formulario
    categoria_seleccionada = request.GET.get('categoria', '')

    # Si se selecciona "Mostrar todos" o no se selecciona ninguna categoría, mostrar todos los productos
    if categoria_seleccionada == '' or categoria_seleccionada == 'Mostrar todos':
        productos = Producto.objects.all()
    else:
        # Filtrar los productos según la categoría seleccionada
        productos = Producto.objects.filter(categoria=categoria_seleccionada)

    return render(request, 'gestion/gestion.html', {
        'productos': productos,
        'categorias': categorias,  # Lista estática de categorías
        'categoria_seleccionada': categoria_seleccionada,
        'user': request.user,
    })


@csrf_exempt
def procesar_venta(request):
    if request.method == "POST":
        productos_vendidos = request.POST.getlist("productos[]")
        cantidades_vendidas = request.POST.getlist("cantidades[]")
        # Verificar los datos recibidos
        print(productos_vendidos)  # Debería mostrar ['24', '27']
        print(cantidades_vendidas)
        
        try:
            for producto_id, cantidad in zip(productos_vendidos, cantidades_vendidas):
                producto = get_object_or_404(Producto, id=producto_id)
                cantidad = int(cantidad)

                # Verificar si hay stock suficiente
                if cantidad > producto.stock:
                    return JsonResponse({'success': False, 'error': f'Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}'})
                
                # Actualizar el stock
                producto.stock -= cantidad
                producto.save()
            
            return JsonResponse({'success': True, 'message': 'Venta procesada exitosamente.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Método no permitido'})

def verificar_stock(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return JsonResponse({'stock': producto.stock})

def editar_producto(request):
    if request.method == "POST":
        producto_id = request.POST.get('productoId')
        nombre = request.POST.get('nombreProducto')
        fecha_vencimiento = request.POST.get('fechaVencimiento')
        categoria = request.POST.get('categoria')
        
        # Buscar el producto a editar
        producto = get_object_or_404(Producto, id=producto_id)
        
        # Actualizar los campos
        producto.nombre = nombre
        producto.fecha_vencimiento = fecha_vencimiento
        producto.categoria = categoria
        producto.save()

        # Retornar la respuesta en formato JSON
        return JsonResponse({'mensaje': 'Producto actualizado correctamente'})

def eliminar_producto(request, producto_id):
    if request.method == 'POST':
        try:
            producto = Producto.objects.get(id=producto_id)
            producto.delete()
            return JsonResponse({'mensaje': 'Producto eliminado exitosamente'})
        except Producto.DoesNotExist:
            return JsonResponse({'error': 'Producto no encontrado'}, status=404)
    return JsonResponse({'error': 'Método no permitido'}, status=405)

def gestion(request):
    es_admin = request.user.groups.filter(name='Administradores').exists()

    productos = Producto.objects.all()
    categorias = [
        "Lacteos", "Embutidos", "Rotiseria", "Limpieza", "Congelados",
        "Confites", "Panaderia", "Snacks", "Dulces", "Bebidas", "Jugos"
    ]
    return render(request, 'gestion/gestion.html', {
            'productos': productos,
            'categorias': categorias,
            'es_admin': es_admin,
    })

def agregar_producto(request):
    if request.method == 'POST':
        datos = request.POST
        categorias_validas = [
            "Lacteos", "Embutidos", "Rotiseria", "Limpieza", "Congelados",
            "Confites", "Panaderia", "Snacks", "Dulces", "Bebidas", "Jugos"
        ]
        categoria = datos['categoria']
        if categoria not in categorias_validas:
            return JsonResponse({'error': 'Categoría no válida'}, status=400)
        
        nombre = datos['nombreProducto']
        valor_compra = int(datos['valorCompra'])
        unidades = int(datos['unidades'])
        porcentaje_ganancia = int(datos['porcentajeGanancia']) / 100
        fecha_vencimiento = datos['fechaVencimiento']
        categoria = datos['categoria']

        # Calcular precio unitario
        precio_unitario = (valor_compra / unidades) * (1 + porcentaje_ganancia)

        # Verificar si el producto ya existe
        producto_existente = Producto.objects.filter(nombre=nombre).first()

        if producto_existente:
            producto_existente.stock += unidades
            producto_existente.save()  # Actualizar el producto existente
        else:
            # Crear un nuevo producto
            producto = Producto.objects.create(
                nombre=nombre,
                precio_unitario=round(precio_unitario, 2),
                fecha_vencimiento=fecha_vencimiento,
                stock=unidades,
                categoria=categoria
            )
        productos = Producto.objects.all()  # Obtener todos los productos después de agregar el nuevo
        return JsonResponse({'mensaje': 'Producto agregado exitosamente', 'productos': list(productos.values())})

    return JsonResponse({'error': 'Método no permitido'}, status=405)