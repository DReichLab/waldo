import re

PLATE_ROWS = 'ABCDEFGH'
PLATE_WELL_COUNT = 96
PLATE_WELL_COUNT_HALF = PLATE_WELL_COUNT // 2
		
def validate_row_letter(letter):
	if len(letter) != 1:
		raise ValidationError(
			_('Row letter %(letter)s must be 1 character.'),
			params={'letter': letter},
		)
	if letter not in PLATE_ROWS:
		raise ValidationError(
			_('Row letter %(letter)s is out of allowed A-H range.'),
			params={'letter': letter},
		)
		
class PlateDomainError(ValueError):
	pass

# domain is [0,PLATE_WELL_COUNT)
def check_plate_domain(int_val):
	if int_val < 0 or int_val >= PLATE_WELL_COUNT:
		raise PlateDomainError(f'{int_val} is out of range for a plate location')

# map integer in domain [0,PLATE_WELL_COUNT) to row and column pair (A, 1)
# order is column first, then row (A1, B1, ..., H1, A2)
def plate_location(int_val):
	check_plate_domain(int_val)
	row_index = int_val % len(PLATE_ROWS)
	column_index = int_val // len(PLATE_ROWS) + 1
	return PLATE_ROWS[row_index], column_index

# map a plate location (A1, H12) back to an integer in [0,PLATE_WELL_COUNT)
def reverse_plate_location_coordinate(row, column):
	row_int = PLATE_ROWS.index(row)
	int_val = row_int + (column - 1) * len(PLATE_ROWS)
	check_plate_domain(int_val)
	return int_val
	
def reverse_plate_location(plate_location):
	row = plate_location[0]
	column = int(plate_location[1:])
	return reverse_plate_location_coordinate(row, column)

# objects map is a dictionary where each entry has keys:
	#	widget_id: modified object id to avoid HTML issues
	#	position: for example A1 or H12
	#	object_id
def duplicate_positions_check(objects_map):
	ids_in_position = {} # store list of ids in this position
	for identifier in objects_map:
		x = objects_map[identifier]
		position = x['position']
		ids_in_position[position] = ids_in_position.get(position, []) +  [identifier]
	
	position_error_messages = []
	for position in ids_in_position:
		if len(ids_in_position[position]) > 1:
			 position_error_messages += [f'{position}: {", ".join(ids_in_position[position])}']
	if len(position_error_messages) > 0:
		error_message = f'too many items in position\n' + '\n'.join(position_error_messages)
		return error_message
	return None
	
def duplicate_positions_check_db(layout_queryset):
	for i in range(PLATE_WELL_COUNT):
		row, column = plate_location(i)
		at_this_location = layout_queryset.filter(row=row, column=column)
		if len(at_this_location) > 1:
			raise ValueError(f'Too many elements at {row}{column}: {len(at_this_location)}')
	
def occupied_wells(layout_queryset):
	occupied_well_count = 0
	num_non_control_assignments = 0
	for i in range(PLATE_WELL_COUNT):
		row, column = plate_location(i)
		at_this_location = layout_queryset.filter(row=row, column=column)
		if len(at_this_location) > 0:
			occupied_well_count += 1
		non_controls = at_this_location.filter(control_type__isnull=True)
		num_non_control_assignments += len(non_controls)
	return occupied_well_count, num_non_control_assignments
	
# checkboxes have values [layout_element_id]_[content_id]
# where content is a powder, lysate, extract, or library
# return lists
# 1. layout_elements_id
# 2. content_ids without a layout_element_id
def layout_and_content_lists(checkbox_values):
	layout_ids = []
	new_content_ids = []
	for value in checkbox_values:
		layout_id, content_id = value.split('_')
		if len(layout_id) > 0:
			layout_ids.append(int(layout_id))
		else:
			new_content_ids.append(int(content_id))
	return layout_ids, new_content_ids

# update the layout elements in the queryset using the json
# objects map is a dictionary where each entry has keys:
	#	widget_id: modified object id to avoid HTML issues
	#	position: for example A1 or H12
	#	object_id
def update_db_layout(user, objects_map, layout_element_queryset, object_name, property_id_field):
	# propagate changes to database
	for identifier in objects_map:
		x = objects_map[identifier]
		position = x['position']
		#print(identifier, position)
		layout_element = layout_element_queryset.get(id=identifier)
		layout_element.set_position(position)
		layout_element.save(save_user=user)

# convert a database list of layout objects into JSON for rendering in HTML template
def layout_objects_map_for_rendering(layout_elements, object_name, property_id_field):
	objects_map = {}
	for layout_element in layout_elements:
		identifier = layout_element.id
		layout_object = getattr(layout_element, object_name, None)
		if layout_object != None:
			label = getattr(layout_object, property_id_field)
		elif layout_element.control_type != None:
			# label with location to distinguish between controls
			label = f'{layout_element.control_type.control_type} {str(layout_element)}'
		else:
			raise ValueError('layout with unknown content {property_id_field} {layout_element.pk}')
		# remove spaces and periods for HTML widget
		widget_id = f'{label}_{identifier}'.replace(' ','').replace('.','')
		joint = { 'position':f'{str(layout_element)}', 'widget_id':widget_id, 'label': label }
		if identifier in objects_map:
			raise ValueError(f'duplicate key {identifier}')
		else:
			objects_map[identifier] = joint
		print(identifier, joint)
	return objects_map 
		
# This is transposed for python. A-H is across, 1-6 is down
BARCODE_POSITIONS_ALL_STRING = '''
Q1	Q9	Q17	Q2	Q10	Q18	Q3	Q11
Q19	Q4	Q12	Q20	Q5	Q13	Q21	Q6
Q14	Q22	Q7	Q15	Q23	Q8	Q16	Q24
Q25	Q33	Q41	Q26	Q34	Q42	Q27	Q35
Q43	Q28	Q36	Q44	Q29	Q37	Q45	Q30
Q38	Q46	Q31	Q39	Q47	Q32	Q40	Q48'''

BARCODES_BY_POSITION = BARCODE_POSITIONS_ALL_STRING.strip().split()

def barcode_at_position(int_position):
	return BARCODES_BY_POSITION[int_position]
	
# Given a Q barcode label, return a string for the P7 barcode source well (A7, H12, etc.) for it
# Used for robot instructions
def p7_qbarcode_source(q):
	position_left_side = BARCODES_BY_POSITION.index(q)
	position_right_side = position_left_side + PLATE_WELL_COUNT_HALF
	row, column = plate_location(position_right_side)
	return f'{row}{column}'

# column first, then row (A1, B1, ..., H1, A2)
# domain is [0,95]
# p7_offset is based on a global, must be even
# return a pair of Q barcodes (p5, p7)
def barcodes_for_location(int_position, p7_offset):
	if p7_offset % 2 == 1:
		raise ValueError('p7_offset must be even because odd values are used for half of plate')
	check_plate_domain(int_position)
	mod_position = int_position % (PLATE_WELL_COUNT // 2) # position within left or right side
	p5 = barcode_at_position(mod_position)
	left_right_offset = int_position // (PLATE_WELL_COUNT // 2) # left 0, right 1
	p7 = barcode_at_position((mod_position + p7_offset + left_right_offset) % PLATE_WELL_COUNT_HALF)
	return p5, p7
	
# TODO currently double-stranded only
# return a pair of indices (p5, p7) as integers
# expect p5_index_starting to be odd
def indices_for_location(int_position, p5_index_starting):
	row, column = plate_location(int_position)
	# P5s for capture are assigned top and bottom. So one P5 for the top half (All wells A-D), and one P5 for the bottom half (All wells E-H).
	row_num = PLATE_ROWS.index(row)
	p5 = p5_index_starting
	if row_num >= (len(PLATE_ROWS) // 2):
		p5 += 1
	# TODO modulus for number of P5 indices
	if p5 > 48: 
		p5 = 1
	# P7s are ordered going left-right across the rows. A1 -> 1, A12 -> 12, B1 -> 13
	row_length = PLATE_WELL_COUNT // len(PLATE_ROWS)
	p7 = row_num * row_length + column
	return p5, p7

def rotate_plate(layout_element_queryset, user):
	for layout_element in layout_element_queryset:
		layout_element.rotate()
		layout_element.save(save_user=user)
		

# Assuming plate names like ABC.12_XY, ABC.12.U_XY is the rotated version of the same batch type
# We need to match doppleganger (rotated) plate names for new extract NE# batches when the first extract batch fails
# Find strings to match using startswith and endswith for Django querysets
# start ABC.12.U or ABC.12
# end XY
def rotated_name_start_and_end(name_string):
	match = re.fullmatch('([a-zA-Z]+)\.([\d]+)(\.U){0,1}(\.NE[\d]+){0,1}_([A-Z]{2})', name_string)
	if match:
		batch_name = match.group(1)
		number = match.group(2)
		is_rotated = match.group(3) == '.U'
		new_extract_indicator = match.group(4)
		batch_type = match.group(5)
		
		# switch rotation
		rotated = '' if is_rotated else '.U'
		start = f'{batch_name}.{number}{rotated}'
		end = batch_type
		return start, end
	else:
		return None, None
		
def rotated_pair_name(name_string):
	start, end = rotated_name_start_and_end(name_string)
	return f'{start}_{end}'
