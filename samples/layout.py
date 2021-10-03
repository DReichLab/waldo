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
