"""
Management command: python manage.py seed_demo
Creates a demo user with full sample data to showcase the application.
"""
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Crea datos de demo para Constructor Express'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true', help='Eliminar datos existentes antes de crear')

    @transaction.atomic
    def handle(self, *args, **options):
        from users.models import User, ContractorProfile
        from clients.models import Client
        from catalog.models import Product
        from budgets.models import Budget, BudgetItemMaterial, BudgetItemLabor

        email = 'demo@constructorexpress.cl'

        if options['reset']:
            User.objects.filter(email=email).delete()
            self.stdout.write('🗑️  Datos anteriores eliminados')

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'El usuario {email} ya existe. Usa --reset para recrear.'))
            return

        # --- USUARIO ---
        user = User.objects.create_user(
            username='demo_gonzalez',
            email=email,
            password='Demo1234!',
            plan='pro',
        )

        ContractorProfile.objects.create(
            user=user,
            company_name='Construcciones & Gasfitería González Ltda.',
            rut='76.543.210-K',
            rubro='gasfiteria',
            phone='+56 9 8765 4321',
            address='Av. Libertador B. O\'Higgins 1850, Piso 3',
            city='Santiago',
            brand_color='#1e40af',
            budget_validity_days=15,
            payment_terms='50% al inicio de los trabajos, 50% contra entrega conforme.',
            notes_template='Todos los materiales incluyen garantía del fabricante. Trabajos garantizados por 6 meses.',
        )
        self.stdout.write('✅ Usuario y perfil creados')

        # --- CLIENTES ---
        clients_data = [
            {'name': 'María Elena Rodríguez Vega', 'rut': '14.567.890-1', 'phone': '+56 9 1111 2222', 'email': 'maria.rodriguez@gmail.com', 'address': 'Calle Las Rosas 456', 'city': 'Providencia'},
            {'name': 'Carlos Andrés Muñoz Soto', 'rut': '11.222.333-4', 'phone': '+56 9 3333 4444', 'email': 'carlos.munoz@empresa.cl', 'address': 'Av. Apoquindo 3000', 'city': 'Las Condes'},
            {'name': 'Inversiones Santa Rosa SpA', 'rut': '77.888.999-0', 'phone': '+56 2 2555 6666', 'email': 'contacto@santarosa.cl', 'address': 'Calle Agustinas 814', 'city': 'Santiago Centro'},
            {'name': 'Ana Lucía Herrera Poblete', 'rut': '17.654.321-8', 'phone': '+56 9 5555 6666', 'email': 'ana.herrera@mail.com', 'address': 'Pasaje Los Aromos 23', 'city': 'Ñuñoa'},
            {'name': 'Jorge Patricio Fuentes Lagos', 'rut': '12.987.654-3', 'phone': '+56 9 7777 8888', 'email': '', 'address': 'Calle Larga 789', 'city': 'Rancagua'},
        ]
        clients = []
        for cd in clients_data:
            c = Client.objects.create(contractor=user, **cd)
            clients.append(c)
        self.stdout.write(f'✅ {len(clients)} clientes creados')

        # --- PRODUCTOS ---
        products_data = [
            # Gasfitería
            ('Grifería mezcladora baño monocomando', 'gasfiteria', 'un', 62000, 85000),
            ('Grifería mezcladora cocina', 'gasfiteria', 'un', 45000, 62000),
            ('Tubo PVC 4" x 3m', 'gasfiteria', 'un', 3200, 4500),
            ('Tubo PVC 2" x 3m', 'gasfiteria', 'un', 1800, 2800),
            ('Codo PVC 4" 90°', 'gasfiteria', 'un', 850, 1200),
            ('Llave de paso 1/2" esférica', 'gasfiteria', 'un', 6200, 8500),
            ('Sellador de cañerías teflón 10m', 'gasfiteria', 'un', 450, 700),
            ('WC Doble descarga', 'gasfiteria', 'un', 85000, 115000),
            # Materiales
            ('Cemento Sol 25kg', 'materiales', 'bls', 5800, 7200),
            ('Arena lavada (m³)', 'materiales', 'm3', 28000, 38000),
            ('Ladrillo fiscal (millar)', 'materiales', 'un', 95000, 115000),
            ('Porcelanato 60x60 (caja 1.8m²)', 'ceramica', 'un', 18500, 25000),
            ('Adhesivo cerámico 25kg', 'ceramica', 'bls', 5200, 7000),
            ('Fragua blanca 5kg', 'ceramica', 'bls', 2800, 4000),
            # Electricidad
            ('Cable THW 2.5mm x 100m', 'electricidad', 'un', 28000, 36000),
            ('Cable THW 4mm x 100m', 'electricidad', 'un', 45000, 58000),
            ('Interruptor unipolar', 'electricidad', 'un', 2500, 3800),
            ('Enchufle 16A', 'electricidad', 'un', 1800, 2800),
            ('Tablero eléctrico 12 circuitos', 'electricidad', 'un', 35000, 48000),
            # Pintura
            ('Pintura Látex interior 20L', 'pintura', 'un', 22000, 29000),
            ('Pintura esmalte 1L', 'pintura', 'un', 4500, 6500),
            ('Rodillo 23cm con mango', 'pintura', 'un', 3200, 5000),
        ]
        products = []
        for (name, cat, unit, cost, sale) in products_data:
            p = Product.objects.create(
                contractor=user, name=name, category=cat,
                unit=unit, cost_price=cost, sale_price=sale
            )
            products.append(p)
        self.stdout.write(f'✅ {len(products)} productos creados')

        # --- PRESUPUESTOS ---
        budgets_data = [
            {
                'client': clients[0], 'number': 1,
                'title': 'Remodelación completa baño principal - Depto Las Rosas',
                'status': 'aceptado', 'tax_percent': 0,
                'payment_terms': '50% al inicio, 50% contra entrega.',
                'notes': 'Incluye desmontaje de instalación existente y retiro de escombros.',
                'materials': [
                    ('Grifería mezcladora baño monocomando', 'un', 1, 85000),
                    ('WC Doble descarga', 'un', 1, 115000),
                    ('Porcelanato 60x60 (caja 1.8m²)', 'un', 8, 25000),
                    ('Adhesivo cerámico 25kg', 'bls', 3, 7000),
                    ('Fragua blanca 5kg', 'bls', 2, 4000),
                    ('Llave de paso 1/2" esférica', 'un', 3, 8500),
                ],
                'labor': [
                    ('Desmontaje y retiro de instalación existente', 'gl', 1, 45000),
                    ('Impermeabilización de paredes y piso', 'm2', 12, 8500),
                    ('Colocación de porcelanato piso y paredes', 'm2', 20, 12000),
                    ('Instalación grifería, WC y accesorios', 'gl', 1, 85000),
                    ('Terminaciones y limpieza final', 'hr', 4, 15000),
                ],
            },
            {
                'client': clients[1], 'number': 2,
                'title': 'Instalación eléctrica oficinas Apoquindo - Piso 3',
                'status': 'enviado', 'tax_percent': 19,
                'payment_terms': '30% anticipo, 40% avance 50%, 30% entrega.',
                'notes': 'Trabajo a realizarse en horario fuera de oficina (18:00 - 23:00 hrs).',
                'materials': [
                    ('Cable THW 2.5mm x 100m', 'un', 3, 36000),
                    ('Cable THW 4mm x 100m', 'un', 1, 58000),
                    ('Tablero eléctrico 12 circuitos', 'un', 2, 48000),
                    ('Interruptor unipolar', 'un', 12, 3800),
                    ('Enchufle 16A', 'un', 20, 2800),
                ],
                'labor': [
                    ('Tendido de cableado eléctrico general', 'gl', 1, 180000),
                    ('Instalación tableros y circuitos', 'un', 2, 35000),
                    ('Instalación enchufes e interruptores', 'un', 32, 3500),
                    ('Pruebas y certificación', 'gl', 1, 45000),
                ],
            },
            {
                'client': clients[2], 'number': 3,
                'title': 'Proyecto ampliación edificio Santa Rosa — Fase 1',
                'status': 'borrador', 'tax_percent': 19,
                'payment_terms': 'A convenir según avance de obra.',
                'notes': '',
                'materials': [
                    ('Cemento Sol 25kg', 'bls', 80, 7200),
                    ('Arena lavada (m³)', 'm3', 15, 38000),
                    ('Ladrillo fiscal (millar)', 'un', 5, 115000),
                ],
                'labor': [
                    ('Excavación y fundaciones', 'gl', 1, 350000),
                    ('Levantamiento de muros', 'm2', 120, 15000),
                    ('Obra gruesa general', 'gl', 1, 480000),
                ],
            },
            {
                'client': clients[3], 'number': 4,
                'title': 'Pintura interior departamento Ñuñoa',
                'status': 'rechazado', 'tax_percent': 0,
                'payment_terms': '100% contra entrega.',
                'notes': '',
                'materials': [
                    ('Pintura Látex interior 20L', 'un', 4, 29000),
                    ('Rodillo 23cm con mango', 'un', 3, 5000),
                ],
                'labor': [
                    ('Preparación de superficies y masillado', 'm2', 150, 2500),
                    ('Aplicación 2 manos de pintura', 'm2', 150, 4500),
                ],
            },
        ]

        for bd in budgets_data:
            b = Budget.objects.create(
                contractor=user,
                client=bd['client'],
                number=bd['number'],
                title=bd['title'],
                status=bd['status'],
                validity_days=15,
                tax_percent=bd['tax_percent'],
                payment_terms=bd['payment_terms'],
                notes=bd['notes'],
            )
            for i, (name, unit, qty, price) in enumerate(bd['materials']):
                BudgetItemMaterial.objects.create(budget=b, name=name, unit=unit, quantity=qty, unit_price=price, order=i)
            for i, (name, unit, qty, price) in enumerate(bd['labor']):
                BudgetItemLabor.objects.create(budget=b, name=name, unit=unit, quantity=qty, unit_price=price, order=i)

        self.stdout.write(f'✅ {len(budgets_data)} presupuestos creados')

        self.stdout.write('\n' + self.style.SUCCESS('='*50))
        self.stdout.write(self.style.SUCCESS('🎉 DEMO CREADO EXITOSAMENTE'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'  📧 Email:      {email}')
        self.stdout.write(f'  🔑 Contraseña: Demo1234!')
        self.stdout.write(f'  🌐 URL:        http://localhost:8000')
        self.stdout.write(self.style.SUCCESS('='*50) + '\n')
