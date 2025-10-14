# store/management/commands/upload_construction_machines.py
import re
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from store.models import Product, Category

class Command(BaseCommand):
    help = 'Upload construction machines and heavy equipment'
    
    def handle(self, *args, **options):
        # First, create construction machine categories
        self.create_categories()
        
        # Parse and upload all products
        self.upload_products()
    
    def create_categories(self):
        """Create construction machine specific categories"""
        categories = [
            {
                'name': 'Concrete Mixers',
                'slug': 'concrete-mixers',
                'service_type': 'construction-tools',
                'description': 'Concrete mixers for construction sites - self-loading, manual, and pan mixers',
                'icon_class': 'fas fa-blender',
                'color_class': 'primary',
                'display_order': 80
            },
            {
                'name': 'Block Making Machines', 
                'slug': 'block-making-machines',
                'service_type': 'construction-tools',
                'description': 'Automatic and semi-automatic block making machines for construction blocks',
                'icon_class': 'fas fa-cube',
                'color_class': 'success',
                'display_order': 81
            },
            {
                'name': 'Construction Lifting Equipment',
                'slug': 'construction-lifting-equipment', 
                'service_type': 'construction-tools',
                'description': 'Hoists, cranes, and lifting equipment for construction sites',
                'icon_class': 'fas fa-arrow-up',
                'color_class': 'warning',
                'display_order': 82
            },
            {
                'name': 'Construction Accessories',
                'slug': 'construction-accessories',
                'service_type': 'construction-tools', 
                'description': 'Clamps, clips, props, and other construction accessories',
                'icon_class': 'fas fa-tools',
                'color_class': 'info',
                'display_order': 83
            },
            {
                'name': 'Rebar Cutting Tools',
                'slug': 'rebar-cutting-tools',
                'service_type': 'construction-tools',
                'description': 'Manual rebar cutters and steel reinforcement tools', 
                'icon_class': 'fas fa-cut',
                'color_class': 'danger',
                'display_order': 84
            },
            {
                'name': 'Site Equipment',
                'slug': 'site-equipment',
                'service_type': 'construction-tools',
                'description': 'Wheel barrows, pumps, and general construction site equipment',
                'icon_class': 'fas fa-hard-hat',
                'color_class': 'secondary',
                'display_order': 85
            },
            {
                'name': 'Compaction Equipment',
                'slug': 'compaction-equipment',
                'service_type': 'construction-tools',
                'description': 'Rollers and compactors for soil and asphalt compaction',
                'icon_class': 'fas fa-compress-alt',
                'color_class': 'dark',
                'display_order': 86
            }
        ]
        
        for cat_data in categories:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"📁 Created category: {cat_data['name']}"))
    
    def upload_products(self):
        """Upload all construction machine products"""
        raw_data = """
        1 CONCRETE MIXER SELF LOADING 91000
        2 CONCRETE MIXER MANUAL LOADING 43333
        3 CONCRETE MIXER JZC350-DH 113455
        4 CONCRETE MIXER JZC500-DH 141520
        5 CONCRETE MIXER CM400-4C 18633
        6 CONCRETE MIXER CM500-4D 21450
        7 Dry MIXER(1 BAG) 143000
        8 DRY MIXER(1/2 BAG) 110500
        9 PAN MIXER-JQ350 34467
        10 PAN MIXER-JQ500 39000
        11 PAN MIXER-JQ500 W/LININGS 42350
        12 BLOCK MACHINE AUTOMATIC LINE QTJ4-27 234000
        13 BLOCK MACHINE SEMI AUTO WITH 1 MOULD yellow 65910
        14 BLOCK MACHINE SEMI AUTO QTJ4-40 WITH 1 MOULD 70980
        15 DRY MIXER FAN BELT C 134 418
        16 DRY MIXER FAN BELT C 161 418
        17 DRY MIXER FAN BELT C 162 418
        18 DRY MIXER FAN BELT C 163 418
        19 LABANON STEEL PROPS 4 METER 418
        20 ELECTRIC HOIST 300 KGS 21938
        21 CONCRETE TOWER BUCKET 1250 LTS 36400
        22 CONCRETE TOWER BUCKET 500 LTS 28600
        23 CONSTRUCTION CLAMPS 120CM 130
        24 CONSTRUCTION CLAMPS 90CM 104
        25 CONSTRUCTION CLAMPS 150CM 156
        26 CONSTRUCTION CLAMPS 70CM 91
        27 CONSTRUCTION CLIPS-FORMWORK 33
        28 MANUAL REBAR CUTTER 32MM 5720
        29 MANUAL REBAR CUTTER 28MM 4550
        30 MANUAL REBAR CUTTER 22MM 3770
        31 WHEEL BARROW 1TYRE 800
        32 GREASE BUCKET 1701
        33 NETLIFT CRANE NLA 071 7800
        34 Concrete Lifting Machine 39000
        35 Block Machine Automatic PALLET 900*450*20 225
        36 TRUCK TYRE 3 TYRE 7876
        37 DOUBLE DRUM ROLLER DIESEL 600KG 72222
        38 HONDA WATER PUMP 2'' 2095
        39 HONDA WATER PUMP 3'' 2362
        40 CONCRETE CUBE MOULD 8KG 982
        41 GEARBOX FOR JZC350 13293
        42 WHEEL BARROW 2 TYRES 3667
        43 CLIPS TIGHTENING MACHINE 1498
        44 MOBILE CRUSHER MACHINE 39000
        45 NET LIFT DRUMM CARRIER 4395
        46 GALVANIZED STEEL PROPS 4 METER 380
        47 IMER DRY CONCRETE MIXER GREEN 35000
        48 AUTOMATIC MACHINE MOULD 4&5&6&8 13000
        49 AUTOMATIC MACHINE PAVMENT MOULD 15294
        """
        
        lines = raw_data.strip().split('\n')
        created_count = 0
        errors = []
        
        with transaction.atomic():
            for line in lines:
                product_data = self.parse_product_line(line)
                if not product_data:
                    continue
                
                try:
                    # Categorize based on equipment type
                    category_slug = self.categorize_product(product_data['id'], product_data['name'])
                    category = Category.objects.get(slug=category_slug)
                    
                    # Create proper product name
                    proper_name = self.generate_proper_name(product_data['name'])
                    
                    # Create slug
                    slug = re.sub(r'[^\w\s-]', '', proper_name.lower()).strip().replace(' ', '-')[:200]
                    
                    # Ensure unique slug
                    counter = 1
                    original_slug = slug
                    while Product.objects.filter(slug=slug).exists():
                        slug = f"{original_slug}-{counter}"
                        counter += 1
                    
                    # Skip products with price 0 or empty
                    if product_data['price'] == 0:
                        self.stdout.write(
                            self.style.WARNING(f"⚠️ Skipping {product_data['id']:2d}. {proper_name} - Price is 0")
                        )
                        continue
                    
                    # Create product with 10% price increase and 20 stock
                    product = Product(
                        name=proper_name,
                        slug=slug,
                        description=self.generate_description(product_data['name'], category_slug),
                        price=Decimal(product_data['price']),
                        category=category,
                        product_type='tool',
                        stock=20,
                        available=True,
                        apply_price_increase=True  # This applies the 10% increase
                    )
                    product.save()
                    
                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ {product_data['id']:2d}. {proper_name} - ₵{product.price} (Stock: 20)")
                    )
                    
                except Exception as e:
                    errors.append(f"Error {product_data['id']}: {str(e)}")
                    self.stdout.write(
                        self.style.ERROR(f"❌ {product_data['id']:2d}. {product_data.get('name', 'Unknown')} - {e}")
                    )
        
        # Final report
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(f"🎉 UPLOAD COMPLETE: {created_count} construction machines created"))
        self.stdout.write(self.style.SUCCESS(f"💰 All prices include 10% increase"))
        self.stdout.write(self.style.SUCCESS(f"📦 All products have 20 units in stock"))
        
        if errors:
            self.stdout.write(self.style.ERROR(f"❌ {len(errors)} errors:"))
            for error in errors[:10]:
                self.stdout.write(self.style.ERROR(f"  - {error}"))
    
    def parse_product_line(self, line):
        """Parse product line and extract data"""
        line = line.strip()
        if not line or not line[0].isdigit():
            return None
            
        try:
            # Split the line into parts
            parts = line.split()
            if len(parts) < 3:
                return None
            
            # First part is the ID
            item_number = int(parts[0])
            
            # Last part is the price
            try:
                price = Decimal(parts[-1])
            except:
                price = Decimal('0')
            
            # Everything between first and last is the product name
            name_parts = parts[1:-1]
            product_name = ' '.join(name_parts)
            
            return {
                'id': item_number,
                'name': product_name,
                'price': price
            }
            
        except (ValueError, IndexError) as e:
            self.stdout.write(self.style.WARNING(f"⚠️ Could not parse line: {line} - {e}"))
            return None
    
    def categorize_product(self, product_id, product_name):
        """Categorize product based on equipment type"""
        name_lower = product_name.lower()
        
        # CONCRETE MIXERS (1-11, 47)
        if any(word in name_lower for word in ['concrete mixer', 'dry mixer', 'pan mixer', 'jzc', 'jq']):
            return 'concrete-mixers'
        
        # BLOCK MAKING MACHINES (12-14, 35, 48-49)
        elif any(word in name_lower for word in ['block machine', 'automatic machine', 'qtj4', 'pallet', 'mould']):
            return 'block-making-machines'
        
        # LIFTING EQUIPMENT (20-21, 33-34, 45)
        elif any(word in name_lower for word in ['hoist', 'crane', 'bucket', 'lifting', 'lift']):
            return 'construction-lifting-equipment'
        
        # REBAR CUTTING TOOLS (28-30)
        elif any(word in name_lower for word in ['rebar cutter', 'rebar']):
            return 'rebar-cutting-tools'
        
        # COMPACTION EQUIPMENT (37)
        elif any(word in name_lower for word in ['roller', 'compactor']):
            return 'compaction-equipment'
        
        # CONSTRUCTION ACCESSORIES (15-19, 23-27, 32, 40-41, 43, 46)
        elif any(word in name_lower for word in ['belt', 'props', 'clamps', 'clips', 'gearbox', 'grease', 'mould']):
            return 'construction-accessories'
        
        # SITE EQUIPMENT (31, 36, 38-39, 42, 44)
        elif any(word in name_lower for word in ['wheel barrow', 'tyre', 'water pump', 'crusher']):
            return 'site-equipment'
        
        else:
            return 'construction-accessories'  # Default category
    
    def generate_proper_name(self, product_name):
        """Generate proper product name with consistent formatting"""
        name_lower = product_name.lower()
        
        # Concrete Mixers
        if 'concrete mixer self loading' in name_lower:
            return "Self-Loading Concrete Mixer"
        elif 'concrete mixer manual loading' in name_lower:
            return "Manual Loading Concrete Mixer"
        elif 'jzc350-dh' in name_lower:
            return "Concrete Mixer JZC350-DH"
        elif 'jzc500-dh' in name_lower:
            return "Concrete Mixer JZC500-DH"
        elif 'cm400-4c' in name_lower:
            return "Concrete Mixer CM400-4C"
        elif 'cm500-4d' in name_lower:
            return "Concrete Mixer CM500-4D"
        elif 'dry mixer(1 bag)' in name_lower:
            return "Dry Concrete Mixer - 1 Bag Capacity"
        elif 'dry mixer(1/2 bag)' in name_lower:
            return "Dry Concrete Mixer - 1/2 Bag Capacity"
        elif 'pan mixer-jq350' in name_lower:
            return "Pan Mixer JQ350"
        elif 'pan mixer-jq500' in name_lower:
            return "Pan Mixer JQ500"
        elif 'pan mixer-jq500 w/linings' in name_lower:
            return "Pan Mixer JQ500 with Linings"
        
        # Block Machines
        elif 'block machine automatic line qtj4-27' in name_lower:
            return "Automatic Block Making Machine QTJ4-27"
        elif 'block machine semi auto with 1 mould yellow' in name_lower:
            return "Semi-Automatic Block Machine with Mould (Yellow)"
        elif 'block machine semi auto qtj4-40 with 1 mould' in name_lower:
            return "Semi-Automatic Block Machine QTJ4-40 with Mould"
        
        # Accessories
        elif 'dry mixer fan belt' in name_lower:
            size = self.extract_size(product_name)
            return f"Dry Mixer Fan Belt {size}"
        elif 'lebanon steel props 4 meter' in name_lower:
            return "Lebanon Steel Props 4 Meter"
        elif 'galvanized steel props 4 meter' in name_lower:
            return "Galvanized Steel Props 4 Meter"
        elif 'construction clamps' in name_lower:
            size = self.extract_size(product_name)
            return f"Construction Clamps {size}"
        elif 'construction clips-formwork' in name_lower:
            return "Formwork Construction Clips"
        
        # Lifting Equipment
        elif 'electric hoist 300 kgs' in name_lower:
            return "Electric Hoist 300kg Capacity"
        elif 'concrete tower bucket' in name_lower:
            capacity = self.extract_capacity(product_name)
            return f"Concrete Tower Bucket {capacity}"
        elif 'netlift crane nla 071' in name_lower:
            return "Netlift Crane NLA 071"
        elif 'concrete lifting machine' in name_lower:
            return "Concrete Lifting Machine"
        elif 'net lift drum carrier' in name_lower:
            return "Net Lift Drum Carrier"
        
        # Rebar Tools
        elif 'manual rebar cutter' in name_lower:
            size = self.extract_size(product_name)
            return f"Manual Rebar Cutter {size}"
        
        # Site Equipment
        elif 'wheel barrow 1tyre' in name_lower:
            return "Wheel Barrow - Single Tyre"
        elif 'wheel barrow 2 tyres' in name_lower:
            return "Wheel Barrow - Double Tyres"
        elif 'grease bucket' in name_lower:
            return "Grease Bucket"
        elif 'truck tyre 3 tyre' in name_lower:
            return "Truck Tyre - 3 Tyre Set"
        elif 'honda water pump' in name_lower:
            size = self.extract_size(product_name)
            return f"Honda Water Pump {size}"
        elif 'concrete cube mould 8kg' in name_lower:
            return "Concrete Cube Mould 8kg"
        elif 'gearbox for jzc350' in name_lower:
            return "Gearbox for JZC350 Mixer"
        elif 'clips tightening machine' in name_lower:
            return "Clips Tightening Machine"
        elif 'mobile crusher machine' in name_lower:
            return "Mobile Crusher Machine"
        elif 'imer dry concrete mixer green' in name_lower:
            return "Imer Dry Concrete Mixer (Green)"
        elif 'automatic machine mould 4&5&6&8' in name_lower:
            return "Automatic Machine Mould Set (4,5,6,8 inch)"
        elif 'automatic machine pavment mould' in name_lower:
            return "Automatic Machine Pavement Mould"
        elif 'double drum roller diesel 600kg' in name_lower:
            return "Double Drum Roller Diesel 600kg"
        
        else:
            # Default - capitalize properly
            return product_name.title()
    
    def extract_size(self, product_name):
        """Extract size information from product name"""
        import re
        # Look for measurements like 120CM, 32MM, 2'', etc.
        patterns = [
            r'(\d+)\s*cm',
            r'(\d+)\s*mm', 
            r'(\d+)"',
            r'c\s*(\d+)',
            r'(\d+)\s*tyre',
            r'(\d+)\s*meter'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, product_name.lower())
            if match:
                unit = pattern.replace(r'(\d+)\s*', '').replace('"', 'inch').replace("''", "inch")
                return f"{match.group(1)}{unit.upper()}"
        
        return ""
    
    def extract_capacity(self, product_name):
        """Extract capacity information from product name"""
        import re
        match = re.search(r'(\d+)\s*lts', product_name.lower())
        if match:
            return f"{match.group(1)} Liters"
        
        match = re.search(r'(\d+)\s*kgs', product_name.lower())
        if match:
            return f"{match.group(1)} kg"
        
        return ""
    
    def generate_description(self, product_name, category_slug):
        """Generate product description based on equipment type"""
        name_lower = product_name.lower()
        
        # Base descriptions by category
        category_descriptions = {
            'concrete-mixers': 'Professional concrete mixing equipment for construction sites. Durable construction and efficient mixing performance.',
            'block-making-machines': 'Automatic and semi-automatic block making machines for producing construction blocks. High efficiency and reliability.',
            'construction-lifting-equipment': 'Heavy-duty lifting equipment for construction materials and concrete. Safety certified and robust construction.',
            'construction-accessories': 'Quality construction accessories and spare parts for various construction equipment. Ensures optimal performance.',
            'rebar-cutting-tools': 'Manual rebar cutting tools for steel reinforcement work. High leverage design for easy cutting.',
            'site-equipment': 'Essential construction site equipment for material handling and site operations. Durable and practical.',
            'compaction-equipment': 'Soil and asphalt compaction equipment for construction projects. Diesel powered for high performance.'
        }
        
        base_desc = category_descriptions.get(category_slug, 'Professional construction equipment for building and infrastructure projects.')
        
        # Add specific features based on product type
        features = ""
        specifications = ""
        
        if 'concrete mixer' in name_lower:
            if 'self loading' in name_lower:
                features = " Automatic self-loading system. Hydraulic operation. High mixing efficiency. Suitable for large construction projects."
                specifications = " 500L mixing capacity. Diesel engine powered. 360-degree rotation. Built-in water tank."
            elif 'manual' in name_lower:
                features = " Manual loading design. Simple operation. Robust steel construction. Easy maintenance."
                specifications = " 350L capacity. Electric motor. Drum rotation mixing. Portable design."
            elif 'jzc' in name_lower:
                features = " Reversible drum mixer. Dual operation mode. Heavy-duty construction. Reliable performance."
                specifications = " 350L/500L capacity. 5.5KW/7.5KW motor. Drum rotation speed: 15-18 rpm."
            elif 'dry mixer' in name_lower:
                features = " Dry concrete mixing. Uniform mixing quality. Heavy-duty steel body. Easy to clean."
                specifications = " 1 bag/0.5 bag capacity. 3KW electric motor. Powder coating finish."
            elif 'pan mixer' in name_lower:
                features = " Pan-type mixing mechanism. Thorough mixing action. Low maintenance. Suitable for various mixes."
                specifications = " 350L/500L capacity. 4KW/5.5KW motor. Rubber linings available."
        
        elif 'block machine' in name_lower:
            if 'automatic' in name_lower:
                features = " Fully automatic operation. High production capacity. Vibrating compaction. PLC control system."
                specifications = " 2000-3000 blocks per day. 7.5KW power. Hydraulic vibration. Multiple block sizes."
            elif 'semi auto' in name_lower:
                features = " Semi-automatic operation. Manual mould feeding. Mechanical vibration. Easy to operate."
                specifications = " 1000-1500 blocks per day. 4KW power. Manual control. Various mould options."
        
        elif 'hoist' in name_lower:
            features = " Electric powered hoist. Safety brake system. Remote control operation. Heavy-duty construction."
            specifications = " 300kg lifting capacity. 220V operation. 12m/min lifting speed. Steel wire rope."
        
        elif 'rebar cutter' in name_lower:
            features = " Manual hydraulic operation. High leverage design. Clean cutting edges. Portable and durable."
            specifications = " 22mm/28mm/32mm cutting capacity. 4:1 leverage ratio. Heat-treated blades. Safety lock."
        
        elif 'wheel barrow' in name_lower:
            features = " Heavy-duty steel construction. Pneumatic tires. Balanced design. Easy maneuverability."
            specifications = " 100-150kg capacity. Galvanized steel body. Ball bearings. Comfortable handles."
        
        elif 'water pump' in name_lower:
            features = " Honda engine powered. Self-priming design. Portable construction. Reliable performance."
            specifications = " 2inch/3inch discharge. 5.5HP engine. 30-40m head. Cast iron impeller."
        
        elif 'roller' in name_lower:
            features = " Double drum diesel roller. Vibratory compaction. Water sprinkler system. Excellent maneuverability."
            specifications = " 600kg operating weight. 186F diesel engine. Centrifugal clutch. 65cm drum width."
        
        # Add general construction benefits
        benefits = " Built for heavy-duty construction applications. Reliable performance and long service life. Suitable for contractors and construction companies."
        
        return f"{self.generate_proper_name(product_name)}. {base_desc}{features}{specifications}{benefits} Professional quality construction equipment."