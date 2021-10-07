PLATE_ROWS = 'ABCDEFGH'
PLATE_WELL_COUNT = 96
		
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

# column first, then row (A1, B1, ..., H1, A2)
# domain is [0,95]
def plate_location(int_val):
	if int_val < 0 or int_val >= PLATE_WELL_COUNT:
		raise ValueError(f'{int_val} is out of range for a plate location')
	row_index = int_val % len(PLATE_ROWS)
	column_index = int_val // len(PLATE_ROWS) + 1
	return PLATE_ROWS[row_index], column_index

# map a plate location (A1, H12) back to an integer in [0,95]
def reverse_plate_location_coordinate(row, column):
	row_int = PLATE_ROWS.index(row)
	int_val = row_int + (column - 1) * len(PLATE_ROWS)
	if int_val < 0 or int_val >= PLATE_WELL_COUNT:
		raise ValueError(f'{int_val} is out of range for a plate location')
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

# find the layout element with the corresponding identifier
# This is either
# 1. element with object exactly matching identifier
# or
# 2. return the control element with its starting location
def get_layout_element_for_identifier(layout_element_queryset, identifier, object_name, property_id_field):
	try: # noncontrol
		kwargs = {
			'{0}__{1}'.format(object_name, property_id_field): identifier
		}
		layout_element = layout_element_queryset.get(**kwargs)
	except layout_element_queryset.model.DoesNotExist: # control, named with position
		control_type, start_position = identifier.rsplit(' ', 1)
		row = start_position[0]
		column = int(start_position[1:])
		layout_element = layout_element_queryset.get(control_type__control_type=control_type, row=row, column=column)
	return layout_element

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
		layout_element = get_layout_element_for_identifier(layout_element_queryset, identifier, object_name, property_id_field)
		layout_element.set_position(position)
		layout_element.save(save_user=user)

# convert a database list of layout objects into JSON for rendering in HTML template
def layout_objects_map_for_rendering(layout_elements, object_name, property_id_field):
	objects_map = {}
	for layout_element in layout_elements:
		layout_object = getattr(layout_element, object_name, None)
		if layout_object != None:
			identifier = getattr(layout_object, property_id_field)
		elif layout_element.control_type != None:
			# label with location to distinguish between controls
			identifier = f'{layout_element.control_type.control_type} {str(layout_element)}'
		else:
			raise ValueError('ExtractionBatchLayout with neither lysate nor control content f{layout_element.pk}')
		# remove spaces and periods for HTML widget
		joint = { 'position':f'{str(layout_element)}', 'widget_id':identifier.replace(' ','').replace('.','') }
		objects_map[identifier] = joint
		print(identifier, joint)
	return objects_map 
