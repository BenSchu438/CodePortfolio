from django.core.files import File
from django.conf import settings
from django.test import TestCase
from django.utils import timezone

import os
import random
import datetime
from PIL import Image

from .models import *
from .searches import *

class CategoryModelTests(TestCase):	
	#region is_category_safe()
	def test_is_category_safe_with_safe_tree(self):
		'''
		is_category_safe() with a Tree with no loops should return True at every node
		'''
		a = Category(name='A')
		b = Category(name='B', parent=a)
		c = Category(name='C', parent=a)
		d = Category(name='D', parent=b)
		e = Category(name='E', parent=b)
		f = Category(name='F', parent=b)
		nodes = [a, b, c, d, e, f]

		# each one should return true since there is no loops
		for x in nodes:
			self.assertIs(x.is_category_safe(), True)

	def test_is_category_safe_with_looped_tree(self):
		'''
		is_category_safe() with a tree that loops should return False for all categories in the tree.
		This only happens if the root's parent is set to a child node.
		'''
		a = Category(name='A')
		b = Category(name='B', parent=a)
		c = Category(name='C', parent=a)
		d = Category(name='D', parent=b)
		e = Category(name='E', parent=b)
		f = Category(name='F', parent=b)
		g = Category(name='G', parent=c)
		# A's parent is now F, now theres a cycle
		a.parent = f

		nodes = [a, b, c, d, e, f, g]
		for x in nodes:
			self.assertIs(x.is_category_safe(), False)

	def test_is_category_safe_with_single_item(self):
		'''
		is_category_safe() with a single item without a parent should still return True
		'''
		a = Category(name='A')
		self.assertIs(a.is_category_safe(), True)

	def test_is_cateogy_safe_with_single_loop(self):
		'''
		is_category_safe() with a single item looped to should return False
		'''
		a = Category(name='A')
		a.parent = a
		self.assertIs(a.is_category_safe(), False)
	#endregion

	#region get_cascading_category()
	def test_get_cascading_category_with_chain(self):
		'''
		get_cascading_category() should return a string of the full chain, formated like a directory path.
		'''
		cat_1 = 'A'
		cat_2 = 'B'
		cat_3 = 'C'

		half_name = f'{cat_1}/{cat_2}'
		full_name = f'{cat_1}/{cat_2}/{cat_3}'

		a = Category(name=cat_1)
		b = Category(name=cat_2, parent=a)
		c = Category(name=cat_3, parent=b)

		self.assertEqual(a.get_cascading_category(), cat_1)
		self.assertEqual(b.get_cascading_category(), half_name)
		self.assertEqual(c.get_cascading_category(), full_name)

	def test_get_cascading_category_with_loop(self):
		'''
		get_cascading_category() should return only its own name if its got a loop in it, otherwise it could
		result in a infinite recursion.
		''' 
		cat_1 = 'A'
		cat_2 = 'B'
		a = Category(name=cat_1)
		b = Category(name=cat_2, parent=a)
		a.parent=b
		self.assertEqual(a.get_cascading_category(), cat_1)
		self.assertEqual(b.get_cascading_category(), cat_2)

	#endregion

	#region get_category_via_name()
	def test_get_category_via_name_success(self):
		'''
		get_category_via_name() with a success should get a ref to the item
		'''
		category_name = "testing"
		a = Category(name=category_name)
		a.save()

		ref = Category.get_category_via_name(category_name)
		self.assertIs(ref.id, a.id)

	def test_get_category_via_name_fail(self):
		'''
		get_category_via_name() with no result should return None instead of throwing an error
		'''
		ref = Category.get_category_via_name('testing')
		self.assertIs(ref, None)
	#endregion

	#region get_category_batches()
	def test_get_category_batches_with_simple_category(self):
		'''
		get_category_batches() should return all batches marked with a cateogry and none of the others.
		'''
		# Prep testing categoreies
		cat_1 = Category(name='Target')
		cat_1.save()

		# make a collection of 5 hit batches, and populate it with 10 dummy batches that should be 'missed'
		desired_batches = get_dummy_batch_list(5, 'tgcbwsc')
		desired_batches = CategoryModelTests.assign_bulk_category(desired_batches, cat_1)
		get_dummy_batch_list(10, 'tgcbwsc') 
		
		# Test if the results contained all of the desired batches
		assertSuccessfulQuery(cat_1.get_category_batches(), desired_batches)

	def test_get_category_batches_with_cascading_category(self):
		'''
		get_category_batches() on a category with a 'child' should return the batches for themselves AND children.
		'''
		# set up a small binary tree of categories using array layout:
		# left child idx: 2i+1 
		# right child idx: 2i+2 
		cats = [
			Category(name='A'),
			Category(name='B'),
			Category(name='C'),
			Category(name='D'),
			Category(name='E'),
		]
		for i, c in enumerate(cats):
			# dont give parent to A, its the root
			if i != 0: 
				# inverse function of left/right children index 
				parent_idx =  ( i - ( 1 if i%2!=0 else 2 ) ) // 2 
				c.parent = cats[ parent_idx ]
			c.save()

		# generate test batches. d_batches is intentially left as empty. Extra dummy ones added too.
		get_dummy_batch_list(20, 'tgcbwcc')
		a_batches = CategoryModelTests.assign_bulk_category(get_dummy_batch_list(2, 'tgcbwcc_a'), cats[0]) 
		b_batches = CategoryModelTests.assign_bulk_category(get_dummy_batch_list(1, 'tgcbwcc_d'), cats[1])
		c_batches = CategoryModelTests.assign_bulk_category(get_dummy_batch_list(5, 'tgcbwcc_c'), cats[2])
		d_batches = []
		e_batches = CategoryModelTests.assign_bulk_category(get_dummy_batch_list(3, 'tgcbwcc_e'), cats[4])

		# test each category using the sum of 'children' nodes
		assertSuccessfulQuery(cats[0].get_category_batches(), 
						a_batches + b_batches + c_batches + d_batches + e_batches)
		assertSuccessfulQuery(cats[1].get_category_batches(), 
						b_batches + d_batches + e_batches)
		assertSuccessfulQuery(cats[2].get_category_batches(), 
						c_batches)
		assertSuccessfulQuery(cats[3].get_category_batches(), 
						d_batches)
		assertSuccessfulQuery(cats[4].get_category_batches(), 
						e_batches)
	

	def assign_bulk_category(batch_list : list[Batch], category : Category):
		'''
		helper that categorizes every batch passed in with the given category. Returns the same list.
		'''
		for b in batch_list:
			b.unit_id.category = category
			b.unit_id.save()
			b.save()
		return batch_list
	#endregion

	#region category_verify_safe()
	def test_clean(self):
		'''
		Calling save on a Category should call the category_verify_safe() signal, which should throw an exception
		when saving a Category with a loop in it
		'''
		# create a loop and try to save
		a = Category(name='A')
		a.save()
		a.parent = a
		try:
			a.save()
		except ValidationError:
			pass
		
		# refresh reference to 'a' so it matches the database, discarding the local changes made here.
		a = Category.objects.get(id=a.id)
		if a.parent is a:
			raise AssertionError('The loop was still saved when it should\'ve been aborted.')
		
	#endregion


class UnitModelTests(TestCase):
	#region has_units_of_name()
	def test_has_units_of_name_group_test(self):
		'''
		has_units_of_name() should return True if a Unit with the desired name exists, or False otherwise.
		'''
		# List of tests that are tuples of (test_search, expected_result)
		test_cases = [
			('thuongt', True),
			('tgnouht', True),
			('hello_world', False),
			('', False),
			('thu', True)
		]

		# create a ton of dummy batches. We can use the 'code' supplied for the search case as they're 
		# used to name the Unit.
		get_dummy_batch_list(1, test_cases[0][0])
		get_dummy_batch_list(3, test_cases[1][0])

		# do each test
		for case in test_cases:
			self.assertIs(Unit.has_units_of_name(case[0]), case[1])

	#endregion 
	
	#region get_batches_with_unit_name()
	def test_get_batches_with_unit_name_group_test(self):
		'''
		get_batches_with_unit_name() should return every batch that belongs to a certain unit.
		'''
		# get a group of batches, and assign all those to test units
		test_cat = UnitModelTests.get_dummy_category('tgbwungtc')

		test_unit_1 = Unit(name='unit_name_search_test_1', category=test_cat)
		test_unit_2 = Unit(name='unit_name_search_test_2', category=test_cat)
		test_unit_1.save()
		test_unit_2.save()

		# split cleanly between the two
		desired_batches = get_dummy_batch_list(20, 'tgbwungt')
		unit1 = []
		unit2 = []
		for i, batch in enumerate(desired_batches):
			if i%2==0:
				batch.unit_id = test_unit_1
				unit1.append(batch)
			else:
				batch.unit_id = test_unit_2
				unit2.append(batch)

			batch.save()

		# create some extra dummy ones that should be missed in the test
		get_dummy_batch_list(5, 'asdf')

		# test each one specifically, then a group test
		hits = Unit.get_batches_with_unit_name(test_unit_1.name)
		assertSuccessfulQuery(hits, unit1)
		hits = Unit.get_batches_with_unit_name(test_unit_2.name.upper())
		assertSuccessfulQuery(hits, unit2)

		# this partial search should successfully hit both
		hits = Unit.get_batches_with_unit_name('unit_name_search')
		assertSuccessfulQuery(hits, unit1+unit2)

	def test_get_batches_with_unit_name_with_empty_string(self):
		'''
		get_batches_with_unit_name() return nothing if an empty string is passed in.
		'''
		# this should return none 
		get_dummy_batch_list(20, ' tgbwunwn')
		hits = Unit.get_batches_with_unit_name('')
		self.assertIsNone(hits)
		
	#endregion 

	#region get_batches_of_unit()
	def test_get_batches_of_unit_with_batches(self):
		'''
		get_batches_of_unit() should return a queryset of all batches that belong to the unit and no others.
		'''
		# create testing unit and batches
		dummy_cat = UnitModelTests.get_dummy_category('tgbouwbc')
		test_unit = Unit(name='get_batches_of_unit_test', category=dummy_cat)
		test_unit.save()

		# create batches and assign them to the dummy unit
		desired_batches = get_dummy_batch_list(5, 'tgbouwb')
		for batch in desired_batches:
			batch.unit_id = test_unit
			batch.save()
		
		# create dummy batches 
		get_dummy_batch_list(5, 'wgbof_d')

		assertSuccessfulQuery(test_unit.get_batches_of_unit(), desired_batches)
		
	def test_get_batches_of_unit_with_no_batches(self):
		'''
		get_batches_of_unit() should return a queryset of nothing if the unit doesn't have any batches yet.
		'''
		# create test unit
		dummy_cat = UnitModelTests.get_dummy_category('tgbouwnbc')
		test_unit = Unit(name='empty_unit', category=dummy_cat)
		test_unit.save()

		# generate extra batches that should miss
		get_dummy_batch_list(10, 'tgbouwnb')
		assertSuccessfulQuery(test_unit.get_batches_of_unit(), [])

	#endregion 	

	#region has_unit_type_of_name()
	def test_has_unit_type_of_name_group(self):
		'''
		get_unit_type_via_name() should return the relevant UnitType enum based on the string. Capitalization
		shouldn't affect it, but they should be full and exact spellings.
		'''
		# get all tests, (input, expected_result)
		all_tests = [
			('Horde', True),
			('Infantry', True),
			('ChArActEr', True),
			('EPIC CHARACTER', True),
			('VEHICLE', True),
			('monster', True),
			('titan', True),
			('display', True),
			('infan', False),
			('epic', False),
			('Hello World', False),
		]

		# do each test
		fails = []
		for test in all_tests:
			if Unit.has_unit_type_of_name(test[0]) != test[1]:
				fails.append(test[0])
		if len(fails) > 0:
			raise AssertionError(f'The following failed: {str(fails)}')
	
	#endregion 

	#region get_batches_of_unit_type()
	def test_get_batches_of_unit_type_group(self):
		'''
		get_batches_of_unit_type() should return batches of only the kind within their type, with strings
		of any capitalization being accepted too.
		'''
		# get all tests, (input, expected_result)
		all_tests = [
			Unit.UnitType.HORDE,
			Unit.UnitType.INFANTRY,
			Unit.UnitType.CHARACTER,
			Unit.UnitType.EPIC_CHARACTER,
			Unit.UnitType.VEHICLE,
			'Monster',
			'TITAN',
			'display',
		]

		# for each one, create a list of each one, populating into a list. All of them should be enough
		# to replicate a accurate environment.
		desired_results = []
		for test in all_tests:
			desired_results.append(UnitModelTests.get_dummy_batches_of_utype(5, 'asdf' , test))

		# do each test
		fails = []
		for test in zip(all_tests, desired_results):
			try:
				assertSuccessfulQuery( Unit.get_batches_of_unit_type(test[0]) , test[1] )
			except:
				fails.append(test[0])

		if len(fails) > 0:
			raise AssertionError(f'The following failed: {str(fails)}')
	
	def test_get_batches_of_unit_type_with_invalid(self):
		'''
		get_batches_of_unit_type() should return nothing if an invalid option is given.
		'''
		all_tests = [
			'hello world',
			'Tita',
			'isplay',
			7,
		]

		# create batches of units that DO actually exist to create a realistic environment
		all_modes = [
			Unit.UnitType.HORDE,
			Unit.UnitType.INFANTRY,
			Unit.UnitType.CHARACTER,
			Unit.UnitType.EPIC_CHARACTER,
			Unit.UnitType.VEHICLE,
			Unit.UnitType.MONSTER,
			Unit.UnitType.TITAN,
			Unit.UnitType.DISPLAY,
		]
		for mode in all_modes:
			UnitModelTests.get_dummy_batches_of_utype(3, 'asdf' , mode)

		# do each test
		fails = []
		for test in all_tests:
			try:
				assertSuccessfulQuery( Unit.get_batches_of_unit_type(test) , [] )
			except:
				fails.append(test[0])

		if len(fails) > 0:
			raise AssertionError(f'The following failed: {str(fails)}')

	#endregion 	

	#region unit_clean()
	def test_clean(self):
		'''
		clean() for Unit should throw an error when trying to save a unit type that isn't defined.
		'''
		cat = UnitModelTests.get_dummy_category('tuc')
		test_unit = Unit(name='tuc', category=cat, utype='helloworld')

		# try cleaning
		try:
			test_unit.clean()
		except ValidationError:
			return
		
		raise AssertionError('This test did not catch an error that it should have.')

	#endregion

	#region unit_test_helpers
	def get_dummy_category(tag):
		'''
		Returns a category saved and ready to be used in testing.
		'''
		dummy_cat = Category(name=tag)
		dummy_cat.save()
		return dummy_cat
	
	def get_dummy_batches_of_utype(num : int, testing_name : str, utype ):
		'''
		Return a list with the desired number of batches that all have units assigend the utype passed in.
		'''
		batches = get_dummy_batch_list(num, testing_name)
		for b in batches:
			b.unit_id.utype = utype
			b.unit_id.save()
			b.save()

		return batches

	#endregion


class KitModelTests(TestCase):
	#region get_kit_via_name()
	def test_get_kit_via_name_valid(self):
		'''
		get_kit_via_name() should return the kit based on full or partial completions of a name. 
		'''
		kit_names = [
			'kit_1',
			'kit_2',
			'kit_3',
			'kit_4',
			'kit_5',
		]

		desired_results = []
		for kit in kit_names:
			k = Kit(name=kit)
			k.save()
			desired_results.append(k)

		# test if it finds them correctly
		for test in zip(kit_names, desired_results):
			self.assertEqual(Kit.get_kit_via_name(test[0]), test[1])

		# test if it correctly returns None for nonexistant ones
		self.assertIs(Kit.get_kit_via_name('helloworld'), None)
		
	def test_get_kit_via_with_empty_name(self):
		'''
		get_kit_via_name() should return None if an empty string is given.
		'''
		self.assertIs(Kit.get_kit_via_name(''), None)
		
	#endregion

	#region get_batches_of_kit()
	def test_get_batches_of_kit(self):
		'''
		get_batches_of_kit() should return every batch who originated from this kit and no others.
		'''
		test_kit = Kit(name='test_tgbok')
		test_kit.save()

		desired_batches = get_dummy_batch_list(5, 'tgbok')
		for batch in desired_batches:
			batch.kit_id = test_kit
			batch.save()
		
		# add extra dummy batches for accurate test environment
		get_dummy_batch_list(10, 'tgbok_d')

		assertSuccessfulQuery(test_kit.get_batches_of_kit(), desired_batches)
	
	#endregion


class StorageModelTests(TestCase):
	#region move_container(newLocation)
	def test_move_container_with_valid_input(self):
		'''
		move_container(newLocation) should change the location string as well as auto-update the date
		to today's date
		'''
		today = timezone.now().date()
		oldDate = (today - datetime.timedelta(days=1))
		oldLocation = 'Garage Shelf'
		newLocation = 'Bedroom Closet Shelf'
		test_storage = Storage(
			id='T001',
			location=oldLocation,
			last_moved=oldDate)
		test_storage.move_container(newLocation)
		self.assertIs(test_storage.location, newLocation)
		# assertIs failed when comparing the dates despite being the same, using this instead
		if test_storage.last_moved != today:
			raise ValueError('last_moved was not updated to today\'s date')
	#endregion

	#region can_increment_capacity()
	def test_can_increment_capacity_range(self):
		'''
		can_increment_capacity() should return False for out of range and FULL, and True for the rest
		'''
		test_storage = Storage(id='T001')
		# testing range [-1, 5], which represents Storage.Capacity ENUM range with each bound expanded once
		expected_results = [False, True, True, True, True, False, False]
		for x in range(len(expected_results)):
			test_storage.current_cap = x-1
			self.assertIs(test_storage.can_increment_capacity(), expected_results[x])
	#endregion

	#region increment_capacity()
	def test_increment_capacity_with_full_storage(self):
		'''
		increment_capacity() should do nothing if it increments on a FULL container
		'''
		test_storage = Storage(
			id='T001',
			current_cap=Storage.Capacity.FULL)
		test_storage.increment_capacity()
		self.assertIs(test_storage.current_cap, Storage.Capacity.FULL)
	
	def test_increment_capacity_with_empty_storage(self):
		'''
		increment_capacity() should correctly increment up the capacity with single steps.
		It should be able to go from EMPTY to FULL after 4 steps
		'''
		test_storage = Storage(
			id='T001',
			current_cap=Storage.Capacity.EMPTY)
		for x in range(4):
			test_storage.increment_capacity()
			self.assertIs(test_storage.current_cap, x+1)

	def test_increment_capacity_with_invalid_capacity(self):
		'''
		increment_capacity() should throw an error "Cannot increment capacity: current_cap is out of bounds"
		if the capacity is invalid
		'''
		test_storage = Storage(
			id='T001',
			current_cap=(Storage.Capacity.EMPTY - 1))
		try:
			test_storage.increment_capacity()
			raise ValueError('test_increment_capacity_with_invalid_capacity() should\'ve caught an error, but didn\'t')
		except Exception as e:
			if e.__str__() != 'Cannot increment capacity: current_cap is out of bounds':
				raise e
	#endregion

	#region can_decrement_capacity()
	def test_can_decrement_capacity_range(self):
		'''
		can_increment_capacity() should return False for out of range and EMPTY, and True for the rest
		'''
		test_storage = Storage(id='T001')
		# testing range [-1, 5], which represents Storage.Capacity ENUM range with each bound expanded once
		expected_results = [False, False, True, True, True, True, False]
		for x in range(len(expected_results)):
			test_storage.current_cap = x-1
			self.assertIs(test_storage.can_decrement_capacity(), expected_results[x])
	#endregion
	
	#region decrement_capacity()
	def test_decrement_capacity_with_full_storage(self):
		'''
		decrement_capacity() should correctly decrement down the capacity with single steps.
		It should be able to go from FULL to EMPTY after 4 steps
		'''
		test_storage = Storage(
			id='T001',
			current_cap=Storage.Capacity.FULL)
		for x in range(4, 0, -1):
			test_storage.decrement_capacity()
			self.assertIs(test_storage.current_cap, x-1)
	
	def test_decrement_capacity_with_empty_storage(self):
		'''
		decrement_capacity() should do nothing if it decrements on an EMPTY container
		'''
		test_storage = Storage(
			id='T001',
			current_cap=Storage.Capacity.EMPTY)
		
		test_storage.decrement_capacity()
		self.assertIs(test_storage.current_cap, Storage.Capacity.EMPTY)

	def test_decrement_capacity_with_invalid_capacity(self):
		'''
		decrement_capacity() should throw an error "Cannot decrement capacity: current_cap is out of bounds"
		if the capacity is invalid
		'''
		test_storage = Storage(
			id='T001',
			current_cap=(Storage.Capacity.FULL + 1))
		try:
			test_storage.decrement_capacity()
			raise ValueError('test_decrement_capacity_with_invalid_capacity() should\'ve caught an error, but didn\'t')
		except Exception as e:
			if e.__str__() != 'Cannot decrement capacity: current_cap is out of bounds':
				raise e
	#endregion

	#region is_full()
	def test_is_full_with_full_storage(self):
		'''
		is_full() should return true if the container is full, or at it's '4' enum value
		'''
		test_storage = Storage(
			id='T001',
			current_cap=Storage.Capacity.FULL)
		self.assertIs(test_storage.is_full(), True)

	def test_is_full_with_empty_storage(self):
		'''
		is_full() should return false if the container is not full
		'''
		test_storage = Storage(
			id='T001',
			current_cap=Storage.Capacity.EMPTY)
		for x in range(4):
			test_storage.current_cap = x
			self.assertIs(test_storage.is_full(), False)
	#endregion

	#region is_capacity_in_bounds()
	def test_is_capacity_in_bounds_with_valid_values(self):
		'''
		is_capacity_in_bounds() should return True for all values between EMPTY and FULL
		'''
		test_storage = Storage(id='T001')
		for x in range(Storage.Capacity.EMPTY, Storage.Capacity.FULL+1):
			test_storage.current_cap = x
			self.assertIs(test_storage.is_capacity_in_bounds(), True)

	def test_is_capacity_in_bounds_with_invalid_values(self):
		'''
		is_capacity_in_bounds() should return False for values outside the range of EMPTY and FULL
		'''
		test_storage = Storage(id='T001')
		test_storage.current_cap = Storage.Capacity.EMPTY - 1
		self.assertIs(test_storage.is_capacity_in_bounds(), False)
		test_storage.current_cap = Storage.Capacity.FULL + 1
		self.assertIs(test_storage.is_capacity_in_bounds(), False)
	#endregion

	#region TODO get_stored_points()
	def test_get_stored_points(self):
		return
		

	#endregion

	#region TODO get_capacity_string()
	def test_get_capacity_string(self):
		return

	#endregion


class BatchModelTests(TestCase):
	ENUM_LOOKUP = [
			'Unopened', 
			'Building',
			'Magnetizing',
			'Priming', 
			'Painting',
			'Basing',
			'Varnishing',
			'Repairing',
			'Completed',
			]
	
	#region __str__()
	def test_str_simple(self):
		'''
		__str__() for Batch returns the name of the unit that it belongs to instead of its own key.
		'''
		# get test batch and apply the name
		test_batch = get_dummy_batch('tss')

		# see if it matches
		self.assertEqual(str(test_batch), test_batch.unit_id.name)

	def test_str_duplicates(self):
		'''
		__str__() for Batch returns the name of the unit that it belongs, appending an additional number to its 
		end when there are multiple batches of one unit based on the acquisition date.
		'''
		# get test batch
		test_batch_1 = get_dummy_batch('tss_1')
		test_batch_2 = get_dummy_batch('tss_2')

		# make them both match the same unit, causing a 'duplicate'
		test_batch_2.unit_id = test_batch_1.unit_id
		test_batch_2.save()

		# offset the acuisition dates so the first one is the oldest, thus should be given ' 1'
		today = timezone.now().date()
		test_batch_1.kit_id.acqu_date = today - datetime.timedelta(days=1)
		test_batch_2.kit_id.acqu_date = today
		test_batch_1.kit_id.save()
		test_batch_2.kit_id.save()

		# test with the desired added indexing
		self.assertEqual(str(test_batch_1), test_batch_1.unit_id.name+' 1')
		self.assertEqual(str(test_batch_2), test_batch_2.unit_id.name+' 2')
	
	#endregion
	
	#region __gt__()
	def test_gt_standard(self):
		'''
		Batch's __gt__() should determine that the most recently edited batch is 'greater'. 
		'''
		# prep dummy batches
		test_batch_1 = get_dummy_batch('tgs_1')
		test_batch_2 = get_dummy_batch('tgs_2')
		
		# adjust edit dates 
		today = timezone.now().date()
		test_batch_1.edit_date = today
		test_batch_2.edit_date = today - datetime.timedelta(days=1)
		test_batch_1.save()
		test_batch_2.save()

		# do test. Batch 1 should be greater than batch 2
		self.assertTrue(test_batch_1 > test_batch_2)
		self.assertFalse(test_batch_2 > test_batch_1)

	def test_gt_with_equal_edit_dates(self):
		'''
		Batch's __gt__() with two batches that have the same edit_date should instead rely on comparing the 
		__str__() between the two to sort them in alphabetical order. 
		'''
		# prep dummy batches
		test_batch_1 = get_dummy_batch('A_tgs_1')
		test_batch_2 = get_dummy_batch('Z_tgs_2')
		
		# adjust edit dates
		today = timezone.now().date()
		test_batch_1.edit_date = today
		test_batch_2.edit_date = today
		test_batch_1.save()
		test_batch_2.save()

		# do test. Batch 1 should be greater than batch 2 because its unit name should start with 'A'
		self.assertTrue(test_batch_1 > test_batch_2)

	#endregion

	#region __lt__()
	def test_lt_standard(self):
		'''
		Batch's __lt__() should determine which is 'less' based on whichever batch has the oldest edit_date.
		'''
		test_batch_1 = get_dummy_batch('tls_1')
		test_batch_2 = get_dummy_batch('tls_2')
		
		# set batch 1's edit date to oldest, making it the desired 'lesser'
		today = timezone.now()
		test_batch_1.edit_date = today - datetime.timedelta(days=1)
		test_batch_2.edit_date = today
		test_batch_1.save()
		test_batch_2.save()

		# do test, with batch 1 being less than batch 2
		self.assertTrue(test_batch_1 < test_batch_2)
		self.assertFalse(test_batch_2 < test_batch_1)

	#endregion 

	#region get_images()
	def test_get_images_with_single_images(self):
		'''
		get_images() returns a list of one image when theres only one.
		'''
		tag = 'tgiwsi'
		test_batch = get_dummy_batch(tag)

		# generate a few dummy images, making each one's date slightly older
		desired_images = BatchModelTests.create_dummy_images(test_batch, 1, 6, tag)

		# do test but cache the error if there is one so we can delete images it first
		error = None
		try:
			assertSuccessfulQuery(test_batch.get_images(), desired_images)
		except AssertionError as e:
			error = e

		# delete all images before raising error
		clear_test_image_files()
		
		if error:
			raise error
	
	def test_get_images_with_many_images(self):
		'''
		get_images() returns a list of all images associated with the batch, ordered from newest to oldest.
		'''
		tag = 'tgiwmi'
		test_batch = get_dummy_batch(tag)

		# generate a few dummy images, making each one's date slightly older
		desired_images = BatchModelTests.create_dummy_images(test_batch, 4, 6, tag)

		# do test but cache the error if there is one so we can delete images it first
		error = None
		try:
			assertSuccessfulQuery(test_batch.get_images(), desired_images)
		except AssertionError as e:
			error = e

		# delete all images before raising error
		clear_test_image_files()
		
		if error:
			raise error
		
	def test_get_images_with_no_images(self):
		'''
		get_images() returns None if the batch doesn't have any images.
		'''
		tag = 'tgiwni'
		test_batch = get_dummy_batch(tag)

		# generate some files to ensure a realistic environment
		BatchModelTests.create_dummy_images(test_batch, 0, 5, tag)
		
		# do test but cache the error if there is one so we can delete images it first
		error = None
		try:
			self.assertIsNone(test_batch.get_images())
		except AssertionError as e:
			error = e

		# delete all images before raising error
		clear_test_image_files()

		if error:
			raise error

	#endregion

	#region get_thumbnail_url()
	def test_get_thumbnail_url_single_image(self):
		'''
		get_thumbnail_url() returns the URL of the only batch image if theres only one.
		'''
		tag = 'tgtusi'
		test_batch = get_dummy_batch(tag)

		desired_images = BatchModelTests.create_dummy_images(test_batch, 1, 6, tag)

		# do test but cache the error if there is one so we can delete images it first
		error = None
		try:
			self.assertEqual(test_batch.get_thumbnail_url(), desired_images[0].img_path.url)
		except AssertionError as e:
			error = e

		# delete all images before raising error
		clear_test_image_files()

		if error:
			raise error

	def test_get_thumbnail_url_many_images(self):
		'''
		get_thumbnail_url() returns the newest image URL of the batch. 
		'''
		tag = 'tgtumi'
		test_batch = get_dummy_batch(tag)

		# generate a few dummy images, making each one's date slightly older
		desired_images = BatchModelTests.create_dummy_images(test_batch, 4, 6, tag)
		
		# do test but cache the error if there is one so we can delete images it first
		error = None
		try:
			self.assertEqual(test_batch.get_thumbnail_url(), desired_images[0].img_path.url)
		except AssertionError as e:
			error = e

		# delete all images before raising error
		clear_test_image_files()

		if error:
			raise error

	def test_get_thumbnail_url_no_images(self):
		'''
		get_thumbnail_url() returns None if the batch has no BatchImage's associated with it.
		'''
		tag = 'tgtuni'
		test_batch = get_dummy_batch(tag)

		# generate some files to ensure a realistic environment
		BatchModelTests.create_dummy_images(test_batch, 0, 5, tag)

		# do test but cache the error if there is one so we can delete images it first
		error = None
		try:
			self.assertIsNone(test_batch.get_thumbnail_url())
		except AssertionError as e:
			error = e

		# delete all images before raising error
		clear_test_image_files()

		if error:
			raise error

	#endregion

	#region get_stage_string()
	def test_get_stage_string_group_test(self):
		'''
		get_stage_string() returns the string representation of the batch's stage.
		'''		
		# generate batches and assign each one a new stage, and make sure it matches.
		all_batches = get_dummy_batch_list(len(BatchModelTests.ENUM_LOOKUP), 'tgssgt')
		for i, batch in enumerate( all_batches ):
			batch.stage = i
			batch.save()
			self.assertTrue( batch.get_stage_string() in BatchModelTests.ENUM_LOOKUP )

	def test_get_stage_string_with_invalid_stage(self):
		'''
		get_stage_string() returns None if the stage is set to an invalid number. 
		'''
		tests = [
			941, 
			9,
			-10,
		   ]
		
		test_batch = get_dummy_batch('tgsswis')
		for t in tests:
			test_batch.stage = t
			test_batch.save()
			self.assertIsNone(test_batch.get_stage_string())

	#endregion

	#region get_stage_via_name()
	def test_get_stage_via_name_with_valid_names(self):
		'''
		get_stage_via_name() should return the enum (int) given full or mostly complete strings.
		'''
		test_inputs = BatchModelTests.ENUM_LOOKUP.copy() + ['varn', 'paint', 'build']
		test_results = [0, 1, 2, 3, 4, 5, 6, 7, 8] + [6, 4, 1]

		for test in zip(test_inputs, test_results):
			self.assertEqual(Batch.get_stage_via_name(test[0]), test[1])

	def test_get_stage_via_name_with_invalid_names(self):
		'''
		get_stage_via_name() should return None if the input string is too short (below 3 characters) or doesnt match any
		spellings.
		'''
		test_inputs = BatchModelTests.ENUM_LOOKUP.copy()
		for idx, input in enumerate(test_inputs):
			test_inputs[idx] = input[:3]
		test_inputs += ['hello world', 'monster', 'titan', 'vehicle', 'infantry', '0621'] 

		for test in test_inputs:
			self.assertIsNone(Batch.get_stage_via_name(test))

	#endregion

	#region get_batches_of_stage()
	def test_get_batches_of_stage_group(self):
		'''
		get_batches_of_stage() should return batches of only the kind within their stage.
		'''
		# prepare all tests
		all_tests = Batch.Stage.choices

		# for each one, create a list of each one, populating into a list. All of them should be enough
		# to replicate a accurate environment.
		desired_results = []
		for test in all_tests:
			desired_results.append(BatchModelTests.create_dummy_batch_of_stage(5, 'tgbosg' , test[0]))

		# do each test
		fails = []
		for test in zip(all_tests, desired_results):
			try:
				assertSuccessfulQuery( Batch.get_batches_of_stage(test[0][0]) , test[1] )
			except AssertionError:
				fails.append(test[0][1])

		if len(fails) > 0:
			raise AssertionError(f'The following failed: {str(fails)}')
	
	def test_get_batches_of_stage_with_invalid(self):
		'''
		get_batches_of_stage() should return nothing if an invalid option is given.
		'''
		all_tests = [
			'hello world',
			'ainting',
			'tizing',
			'opened',
			'plete',
			'ing',
			9,
		]

		# create batches of stages that DO actually exist to create a realistic environment
		for stage in Batch.Stage.choices:
			BatchModelTests.create_dummy_batch_of_stage(3, 'asdf' , stage[0])

		# do each test, expecting nothing each time
		fails = []
		for test in all_tests:
			try:
				assertSuccessfulQuery( Batch.get_batches_of_stage(test) , [] )
			except AssertionError:
				fails.append(test)

		if len(fails) > 0:
			raise AssertionError(f'The following failed: {str(fails)}')

	#endregion

	#region total_points()
	def test_total_points(self):
		'''
		total_points() should return an int of the total number of points a Batch represents, calculated by 
		multiplying batch's count value with a unit's points value.
		'''
		test_batch = get_dummy_batch('ttp')

		# 10 models * 100 points per should equal 1000
		total_points = 1000
		test_batch.count = 10
		test_batch.unit_id.points = 100

		test_batch.save()
		test_batch.unit_id.save()

		self.assertEqual(test_batch.total_points(), total_points)
	
	#endregion

	#region batch helpers
	def create_dummy_images(target_batch, desired_hit_count, desired_miss_count, tag):
		'''
		Helper that will generate the desired number of hit and miss BatchImages using the tag. All 
		desired records will be set to point at target_batch. Returns list of desired BatchImages.
		'''
		# create base image to use as reference for the batch image
		img_path = f'{BatchImageModelTests.TEST_PATH}{tag}.jpg'
		Image.new('RGB', (100,75)).save(img_path)

		# create all requested images
		desired_images = []
		for i in range((desired_hit_count + desired_miss_count)):
			# BatchImage based on the created image. 
			batch_img = BatchImageModelTests.get_test_batch_image(img_path, f'{tag}_{i}')
			
			# if not yet reached, assign it to the target_batch 
			if i < desired_hit_count:
				batch_img.batch_id = target_batch
				batch_img.upload_date = timezone.now() - datetime.timedelta(days=(1*i))
				desired_images.append(batch_img)
			
			batch_img.save()

		return desired_images

	def create_dummy_batch_of_stage(count, tag, stage):
		'''
		Helper to create a list of batches with the desired stage. 
		'''
		batches = get_dummy_batch_list(5, tag)
		for b in batches:
			b.stage = stage
			b.save()
		return batches

	#endregion


class BatchImageModelTests(TestCase):
	TEST_PATH = './media/tests/'

	#region compress_image()
	def test_compress_image_and_try_compress_hook(self):
		'''
		compress_image() is automatically called by try_compress() hook. After uploading any image, it 
		should be findable and return 'True' via the is_image_compressed() function. 
		'''
		# create test image
		test_img = self.TEST_PATH + 'test_upload_uncompressed.png'
		Image.new('RGBA', (4000, 2000)).save(test_img)

		# create test record  
		test_batch = get_dummy_batch('tciatch')
		test_batch_img = BatchImage(
			batch_id = test_batch,
			upload_date = timezone.now().date()
		)

		# save the image to the system, which will call the try_compress() hook and should compress the image 
		source_file = File(open(test_img, 'rb'))
		test_batch_img.img_path.save( os.path.basename(test_img) , source_file, save=True)
		source_file.close()

		# delete the original test image
		os.remove(test_img)

		# cache the error first so the source image can be deleted before raising the error
		error = None
		try:
			self.assertIs( BatchImage.is_image_compressed(test_batch_img.img_path.path), True)
		except Exception as e:
			error = e
		
		test_batch_img.delete()
		if error:
			raise e
	#endregion

	#region is_image_compressed()
	def test_is_image_compressed_group_test(self):
		'''
		is_image_compressed() tests for images being .jpgs, a 4:3/3:4 aspect ratio, and being under 
		the max resolution limit. It should return the same bool thats in the file name tuple
		'''
		# create all test images for each edge case. It uses paths so just save the paths.
		
		test_name_list = [
			(self.TEST_PATH+'bad_file_test.png', False),
			(self.TEST_PATH+'bad_ratio_test.jpg', False),
			(self.TEST_PATH+'bad_res_test.jpg', False),
			(self.TEST_PATH+'success_portrait_test.jpg', True),
			(self.TEST_PATH+'success_landscape_test.jpg', True),
		]
		Image.new('RGBA', (2000, 1500)).save(test_name_list[0][0])
		Image.new('RGB', (1000, 1000)).save(test_name_list[1][0])
		Image.new('RGB', (3750, 5000)).save(test_name_list[2][0])
		Image.new('RGB', (1500, 2000)).save(test_name_list[3][0])
		Image.new('RGB', (1000, 750)).save(test_name_list[4][0])

		# do each test sequentially. Do all tests before printing out the assert errors
		fails = []
		for test in test_name_list:
			p = test[0]
			try:
				self.assertIs(BatchImage.is_image_compressed(test[0]), test[1])
			except:
				fails.append(test)

			# delete while you go
			os.remove(p)
		
		if len(fails) > 0:
			raise AssertionError('test_is_image_compressed_group_test(self) failed on the ' + 
						'following tests: ' + str(fails))

	def test_is_image_compressed_with_no_image(self):
		'''
		is_image_compressed() without any valid image path should return None instead of a bool.
		'''
		self.assertIsNone(BatchImage.is_image_compressed('./helloworld.jpg'))

	#endregion

	#region convert_image()
	def test_convert_image_with_no_image(self):
		'''
		convert_image() should throw a ReferenceError if no image is passed in.
		'''
		try:
			test_batch_img = BatchImage.convert_image(None)
		except ReferenceError:
			return 
		raise AssertionError('convert_image() shouldve thrown a ReferenceError, but it didnt.')

	def test_convert_image_with_closed_image(self):
		'''
		convert_image() should throw an error if a closed image is passed in. 
		'''
		img = Image.new('RGB', (2, 2))
		img.close()
		try:
			test_batch_img = BatchImage.convert_image(img)
		except ValueError:
			return 
		raise AssertionError('convert_image() shouldve thrown a ValueError, but it didnt.')
		
	def test_convert_image_with_large_image(self):
		'''
		convert_image() should convert a large image into one that matches the requirements to pass
		'is_image_compressed()' test.
		'''
		# create group of images to test with
		test_name_list = [
			self.TEST_PATH+'bad_file_test.png',
			self.TEST_PATH+'bad_ratio_test.jpg',
			self.TEST_PATH+'bad_res_test.jpg',
			self.TEST_PATH+'success_portrait_test.jpg',
			self.TEST_PATH+'success_landscape_test.jpg',
		]
		Image.new('RGBA', (2000, 1500)).save(test_name_list[0]) 
		Image.new('RGB', (1000, 1000)).save(test_name_list[1])
		Image.new('RGB', (3750, 5000)).save(test_name_list[2])
		Image.new('RGB', (1500, 2000)).save(test_name_list[3])
		Image.new('RGB', (1000, 750)).save(test_name_list[4])

		# do each test sequentially. Do all tests before printing out the assert errors
		test_save_location = self.TEST_PATH+'convert_large_temp.jpg'
		fails = []
		for path in test_name_list:
			original_img = Image.open(path)
			try:
				new_image = BatchImage.convert_image(original_img)
				new_image.save(test_save_location)

				original_img.close()
				new_image.close()

				self.assertIs(BatchImage.is_image_compressed(test_save_location), True)
			except Exception as e:
				fails.append(path)

			# delete test image while you go
			os.remove(path)

		# delete the temp image too
		os.remove(test_save_location)

		if len(fails) > 0:
			raise AssertionError('test_is_image_compressed_group_test(self) failed on the ' + 
						'following tests: ' + str(fails))

	def test_convert_image_with_small_image(self):
		'''
		convert_image() should not make a small image larger than its original size. Its largest dimension
		should remain at the same.
		'''
		test_name_list = [
			self.TEST_PATH+'small_portrait.jpg',
			self.TEST_PATH+'small_landscape.jpg',
		]
		max_dimension = 500
		Image.new('RGB', (400, max_dimension)).save(test_name_list[0])
		Image.new('RGB', (max_dimension, int(max_dimension*0.75))).save(test_name_list[1])

		fails = []
		for path in test_name_list:
			# convert image
			original_img = Image.open(path)
			new_img = BatchImage.convert_image(original_img)
			original_img.close()

			# check the max dimension, make sure it remains the same
			new_max = max(new_img.width, new_img.height)
			try:
				self.assertEqual(new_max, max_dimension)
			except AssertionError:
				fails.append(path)
			new_img.close()

			# cleanup tests
			os.remove(path)

		if len(fails) > 0:
			raise AssertionError('test_convert_image_with_small_image(self) failed on the ' + 
						'following tests: ' + str(fails))
		
	#endregion

	#region get_working_ratio()
	def test_get_working_ratio_portrait(self):
		'''
		get_working_ratio() should return a tuple containing the multipliers to achieve the desired ratio.
		Portrait varient will return a smaller width multiplier.
		'''
		# test last updated when desired ratio was 3:4 in portrait
		self.assertEqual(BatchImage.get_working_ratio(True), (0.75, 1))

	def test_get_working_ratio_landscape(self):
		'''
		get_working_ratio() should return a tuple containing the multipliers to achieve the desired ratio.
		Landscape varient will return a smaller height multiplier.
		'''
		# test last updated when desired ratio was 3:4 in landscape
		self.assertEqual(BatchImage.get_working_ratio(False), (1, 0.75))

	#endregion

	#region batchimage_delete_img()
	def test_delete_img_signal(self):
		'''
		delete_img() should be automatically called after deleting the record of a batch image and delete the 
		image file in uploads.
		'''
		# create image file to test
		test_img_path = self.TEST_PATH + 'test_delete_img.jpg'
		img = Image.new('RGB', (1000, 750))
		img.save(test_img_path)
		img.close()

		# create batch item and grab destination path, and delete original
		test_batch_image = BatchImageModelTests.get_test_batch_image(test_img_path, 'tdis')
		dest_path = test_batch_image.img_path.path
		os.remove(test_img_path)

		# check if it was actually created
		if not os.path.exists(dest_path):
			raise FileNotFoundError(f'Could not find the image that shouldve been uploaded to: {dest_path}')

		# delete to trigger the delete_img() hook
		test_batch_image.delete()
		
		# now check if the image was also deleted
		if os.path.exists(dest_path):
			os.remove(dest_path)
			raise AssertionError('The image at the location still exists when it shouldn\'t.')
		
	#endregion

	#region batchimage_delete_old()
	def test_delete_old_signal(self):
		'''
		delete_old() should be automatically called after saving the file and, if there was a new file uploaded
		to it, it should automatically delete the old.
		'''
		# create 'original' image file to test
		old_test_img = self.TEST_PATH + 'test_delete_old_original.jpg'
		img = Image.new('RGB', (1000, 750))
		img.save(old_test_img)
		img.close()

		# create batch image and grab destination path
		test_batch_image = BatchImageModelTests.get_test_batch_image(old_test_img, 'tdos')
		old_dest_path = test_batch_image.img_path.path

		# create the new image
		new_test_img = self.TEST_PATH + 'test_delete_old_new.jpg'
		img = Image.new('RGB', (750, 1000))
		img.save(new_test_img)
		img.close()

		# update the batch image with the new file, uploading the image and calling the 'delete_old()' signal 
		source_file = File(open(new_test_img, 'rb'))
		test_batch_image.img_path.save(os.path.basename(new_test_img), source_file, save=True)
		source_file.close()

		test_batch_image.save()
		new_dest_path = test_batch_image.img_path.path

		# check if the old image was deleted
		if os.path.exists(old_dest_path):
			os.remove(old_dest_path)
			os.remove(new_dest_path)
			os.remove(old_test_img)
			os.remove(new_test_img)
			raise AssertionError('The image at the location still exists when it shouldn\'t.')
		
		# cleanup
		test_batch_image.delete()
		os.remove(new_test_img)
		os.remove(old_test_img)
		
		
	#endregion

	#region batch_image_helpers
	def get_test_batch_image(file_path, test_code : str):
		'''
		Helper function that returns a batch image using the image in MiniatureGallery/static/tests/.
		test_code is for uniqueness. As it can't be too long, typical codes are acronyms of the calling function.
		If its not found, an error will be thrown. Remember to delete the image after!
		'''
		# prepare paths to the test images
		source_path = file_path      

		# raise error if the static img wasn't found
		if not os.path.isfile( source_path ):
			raise LookupError(f'Could not find static file at {source_path}')

		try:
			# get a batch for testing. Pass in test_code to uniquely identify the record
			test_batch = get_dummy_batch(test_code)
			test_batch_img = BatchImage(
				batch_id = test_batch,
				upload_date = timezone.now().date()
			)

			# get the image file and save it
			source_file = File(open(source_path, 'rb'))
			new_name = f'{test_code}.jpg'
			test_batch_img.img_path.save(os.path.basename(new_name), source_file, save=True)			
			test_batch_img.save()

			source_file.close()

			return test_batch_img
		
		except Exception as e:
			# check if the image was created before the error, deleting it if so
			if os.path.isfile( source_path ):
				os.remove(source_path)
				
			raise e
	#endregion


class TagModelTests(TestCase):
	#region get_tag_via_name()
	def test_get_tag_via_name_group(self):
		'''
		get_tag_via_name() should return the tag object if the passed in name is correct. 
		'''
		# prepare tests for a hit and multiple misses
		hit_test = 'test'
		miss_tests = [
			'tes',
			'est',
			'hello_world',
			'',
		]
		# create test tag
		desired_tag = Tag(name=hit_test)
		desired_tag.save()

		# create a similar tag to emulate a more complex environment
		special_miss_tag = Tag(name=(hit_test)+'_5')
		special_miss_tag.save()

		# see if the desired tag was found, and the misses missed.
		self.assertEqual(Tag.get_tag_via_name(hit_test), desired_tag)
		for test in miss_tests:
			self.assertIsNone(Tag.get_tag_via_name(test))
	
	#endregion
	
	#region get_tagged_batches()
	def test_get_tagged_batches(self):
		'''
		get_tagged_batches() should return only batches that are given the desired tag.
		'''
		test_tag = Tag(name='test_tgtb')
		test_tag.save()

		# create batches and apply the desired tag
		desired_batches = get_dummy_batch_list(5, 'tgtb')
		for batch in desired_batches:
			assignment = TagAssignment(tag_id=test_tag, batch_id=batch)
			assignment.save()
		
		# create extra values to complicate search. Divide evenly between no tag, dummy tag 1, and dummy tag 2
		dummy_tag_1 = Tag(name='dummy_1_tgtb')
		dummy_tag_2 = Tag(name='dummy_2_tgtb')
		dummy_tag_1.save()
		dummy_tag_2.save()
		dummies = get_dummy_batch_list(15, 'tgtb_d')
		for i, d in enumerate(dummies):
			assignment = None
			if i % 3 == 0:
				continue
			else: 
				assignment = TagAssignment(tag_id= ( dummy_tag_1 if i%3==1 else dummy_tag_2 ), batch_id=d)
				assignment.save()
		
		# run the test
		assertSuccessfulQuery(test_tag.get_tagged_batches(), desired_batches)

	#endregion
	

class TagAssignmentModelTests(TestCase):
	# TagAssignment has no tests for now.
	pass


class SearchFunctionsTests(TestCase):
	#region TODO wide_db_search()
	
	# this is going to be too many large tests for now, so will do later when time permits

	#endregion

	#region is_valid_search_string()
	def test_is_valid_search_string_with_valid_strings(self):
		'''
		is_valid_search_string() should return True strings that arent just random punctuation.
		'''
		tests = [
			'necron',
			'   infantry  ',
			'-paint space marine~~~',
			'necron stage world hello hi!',
			' ;fdfdsa ',
			'---==hi=+++_',
			" ,./<>?;':\"\\[]}necron{|=-`~_+)(*&^%$#@!"
		]
		for t in tests:
			self.assertTrue(is_valid_search_string(t))

	def test_is_valid_search_string_with_invalid_strings(self):
		'''
		is_valid_search_string() should return False for strings that are only punctuation or empty.
		'''
		tests = [
			'',
			'>?<',
			'\\\\\\\\\\\\\\\\\\\\\\\\\\\\',
			'\'\'\'\'\'\'',
			' )(%));.',
			'            ',
			'.',
			':)',
			':(',
			';_;',
		]
		for t in tests:
			self.assertFalse(is_valid_search_string(t))
	#endregion

	#region parse_search_string()
	def test_parse_search_string_with_simple_strings(self):
		'''
		parse_search_string() should convert a string of words into a list of each individual word/phrase.
		Any underscores should be processed into spaces for single keywords.
		'''
		# test tuples as (input, desired result)
		tests = [
			('necron world unopened', ['necron', 'world', 'unopened']), 
			('painting', ['painting']), 
			('space_marine epic_character', ['space marine', 'epic character']), 
		]

		for t in tests:
			self.assertEqual(parse_search_string(t[0]), t[1])

	def test_parse_search_string_with_complex_strings(self):
		'''
		parse_search_string() should be able to remove large chunks of punctuation to clean the search.
		'''
		# test tuples as (input, desired result)
		tests = [
			('  necron        world                 unopened       ', 
				['necron', 'world', 'unopened']), 
			('___________painting_______________', 
				['painting']), 
			('space_marine )(*&^%$#@! epic_character', 
				['space marine', 'epic character']), 
			('<html></html>',
				['html', 'html']),
			('test<html></html>injection',
				['test', 'html', 'html', 'injection']),
		]

		for t in tests:
			self.assertEqual(parse_search_string(t[0]), t[1])

	def test_parse_search_string_with_empty_string(self):
		'''
		parse_search_string() should return an empty list if given an empty string.
		'''
		self.assertEqual(parse_search_string(''), [])
	
	def test_parse_search_string_with_large_string(self):
		'''
		parse_search_string() shouldn't have any issues with large strings and just truncate instead.
		'''
		# this should be truncated during the spaces and thus, return empty list
		test_big_string = ('           ' * 100) + 'necron'
		self.assertEqual(parse_search_string(test_big_string), [])

	#endregion


#region general helpers

def assertSuccessfulQuery(query_hits, desired_hits):
		'''
		Helper that will throw a AssertionError if either the query_hits is missing a desired hit OR if query_hits
		has contents that arent in desired_hits.
		'''
		# convert if its just a queryset
		if not isinstance(query_hits, list):
			query_hits = list(query_hits)

		fails = []
		for batch in desired_hits:
			if batch not in query_hits:
				fails.append(batch)
		if len(fails) > 0:
			raise AssertionError('The query hits did not contain the following: ' + str(fails))
		
		# Test if the results contained MORE than than it should've.
		elif len(query_hits) > len(desired_hits):
			raise AssertionError('The query resulted in more hits than it was supposed to.')


def get_dummy_batch_list(count : int, testing_name : str):
	'''
	Returns a list that contains the desired number of dummy batches for testing.
	'''
	all_batches = []
	for i in range(count):
		all_batches.append(get_dummy_batch(testing_name))

	return all_batches


def get_dummy_batch(testing_name : str):
	'''
	Helper function that returns a dummy batch record for testing. 
	Populates its unit/kit/storage fields with dummy records too.
	'''
	# generate a random tag to prevent clashes and make it clear where the test came from, incase any errors
	# arise later and they manage to get populated into the actual database.
	ran_tag = random.randint(0, 99999)
	if ran_tag == 69 or ran_tag == 420:
		print('nice')
	ran_tag = f'_{testing_name}_{ran_tag:.5f}'

	# create all dummy records with the given tag
	test_category = Category(name = f'cat_{ran_tag}')
	test_unit = Unit(name = f'unit_{ran_tag}', category = test_category)
	test_kit = Kit(name = f'kit_{ran_tag}')
	test_storage = Storage(id = f'storage_{ran_tag}')
	test_batch = Batch(
		note = f'batch_{ran_tag}', 
		unit_id = test_unit,
		kit_id = test_kit,
		storage_id = test_storage
	)

	# save all dummy records
	test_category.save()
	test_unit.save()
	test_kit.save()
	test_storage.save()
	test_batch.save()

	return test_batch

def clear_test_image_files():
	'''
	Deletes all BatchImage records and the files associated with them.
	'''
	# delete any spare pictures created in the test path. HARDCODE check to make sure no errors are made
	if BatchImageModelTests.TEST_PATH != './media/uploads/':
		for img in os.listdir(BatchImageModelTests.TEST_PATH):
			os.remove(BatchImageModelTests.TEST_PATH+img)
	else:
		raise SyntaxError('BatchImageModelTests.TEST_PATH has been set to the uploads path.' + 
					' Correct this as otherwise, it will wipe all images in the actual database.')

	# the delete hook auto deletes the file 
	for img in BatchImage.objects.all():
		img.delete()

#endregion