from django.db import models
from django.db.models.signals import pre_delete, post_save, pre_save
from django.contrib import admin
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.conf import settings
from django.dispatch import receiver
from PIL import Image, ImageOps
import os

# Models are organized by their table heiarchy. Parent tables at the top, and child tables are lower.

class Category(models.Model):
	'''
	A collection of categories that can be assigned to multiple units. Differs from 'Tag' as each
	unit can only have one type of this cateogry.
	These categories are intended to be the media source the model is based on, such as Warhammer.
	'''
	class Meta:
		verbose_name = 'Category'
		verbose_name_plural = 'Categories'

	name = models.CharField(
		max_length=32, 
		blank=False,
		verbose_name='Category Name')
	parent = models.ForeignKey(
		'self', 
		null=True, 
		blank=True,
		on_delete=models.SET_NULL, 
		verbose_name='Parent Category')


	def __str__(self):
		return self.name
	
	@admin.display(boolean=True, ordering="name", description="safe?")
	def is_category_safe(self):
		'''
		Returns whether or not the hierarchy contains any loops.
		Has admin display settings for admin menu.
		'''
		visited = [self]
		next_node_ptr = self.parent
		while next_node_ptr:
			visited.append(next_node_ptr)
			# if multiple found, then a loop has been found
			if visited.count(next_node_ptr) > 1:
				if settings.DEBUG:
					print(self.name + " is part of a infinite category loop! " + visited.__str__())
				return False
			else:
				next_node_ptr = next_node_ptr.parent
		else:
			return True

	def get_cascading_category(self):
		'''
		Get the name String that includes all parents, organized like a file structure.
		'''
		if self.is_category_safe():
			full_str = ''
			if self.parent is not None:
				full_str += self.parent.get_cascading_category() + '/'
			return (full_str + self.name)
		else:
			return self.name
	
	def get_category_via_name(category_name):
		'''
		Get a reference of Category by name if it exists, or None if it doesn't
		'''
		# get() always throws an exception with no items, so catch it and return None instead
		try:
			# remove 's' at the end to avoid false negatives due to plural spelling
			if category_name.__str__()[-1] == 's':
				category_name = category_name[0:-1]
			return Category.objects.get(name__icontains=category_name)
		except: 
			return None

	def get_category_batches(self):
		'''
		Get a list of all batches from this Category and all subcategories.
		'''
		# do safety check first, lest infinite loop be upon ye
		if not self.is_category_safe():
			return []
		
		# using DFS
		batch_list = []
		categories_stack = [self]
		while len(categories_stack) > 0:
			# pop top stack, add children categories
			curr_category = categories_stack.pop()
			categories_stack += Category.objects.filter(parent=curr_category.id)

			# get all units / batches from current category
			#for unit in Unit.objects.filter(category=curr_category.id):
			#    batch_list += unit.get_batches_of_unit()

			# below returns on avg x4 faster than above since its O(1) instead of O(n)
			batch_list += Batch.objects.filter(unit_id__category=curr_category.id)
		
		return batch_list

	def clean(self):
		'''
		Validate that no loop was created as a result of the new save.
		'''
		if not self.is_category_safe():
			raise ValidationError('A category\'s hierarchy cannot form a loop.')


class Unit(models.Model):
	'''
	A collection of character(s) that a miniature represents.
	'''
	class Meta:
		verbose_name = 'Unit'
		verbose_name_plural = 'Units'

	name = models.CharField(
		max_length=128, 
		blank=False,
		verbose_name='Unit Name')
	category = models.ForeignKey(
		Category, 
		on_delete=models.RESTRICT,
		verbose_name='Categorization')
	points = models.IntegerField(
		default=0, 
		verbose_name='Points Per Model')

	class UnitType(models.TextChoices):
		HORDE = 'Horde'
		INFANTRY = 'Infantry'
		CHARACTER = 'Character'
		EPIC_CHARACTER = 'Epic Character'
		VEHICLE = 'Vehicle'
		MONSTER = 'Monster'
		TITAN = 'Titan'
		DISPLAY = 'Display'
	utype = models.CharField(
		max_length=16,
		choices=UnitType,
		default=UnitType.INFANTRY, 
		verbose_name='Unit Type')


	def __str__(self):
		return self.name
	
	def has_units_of_name(unit_name):
		'''
		Returns whether Units with the given name exist or not.
		'''
		try:
			#  remove 's' at the end to avoid false negatives due to plural spelling
			if unit_name[-1].lower() == 's':
				unit_name = unit_name[0:-1]
			return Unit.objects.filter(name__icontains=unit_name).count() > 0
		except:
			return False

	def get_batches_with_unit_name(unit_name):
		'''
		Get a queryset of all Batches that represent the Unit name given. Returns none if 
		empty string is given.
		'''
		if unit_name == '':
			return None
		else:
			try:
				return Batch.objects.filter(unit_id__name__icontains=unit_name)
			except:
				[]

	def get_batches_of_unit(self):
		'''
		Get a queryset of all Batches that this Unit represents.
		'''
		return Batch.objects.filter(unit_id=self)

	def has_unit_type_of_name(type_name):
		'''
		Return whether or not the given unit type exists. 
		'''
		all_cases = [
			Unit.UnitType.HORDE.lower(),
			Unit.UnitType.INFANTRY.lower(),
			Unit.UnitType.CHARACTER.lower(),
			Unit.UnitType.EPIC_CHARACTER.lower(),
			Unit.UnitType.VEHICLE.lower(),
			Unit.UnitType.MONSTER.lower(),
			Unit.UnitType.TITAN.lower(),
			Unit.UnitType.DISPLAY.lower(),
		]
		return all_cases.count(type_name.lower()) > 0
		#try:
		#	u = Unit.objects.filter(utype=type_name).first()
		#	return u != None
		#except Exception as e:
		#	return None

	def get_batches_of_unit_type(unit_type):
		'''
		Get queryset of all Batches that are assigned the given Unit Type Enum.
		'''
		#batches = []
		#for unit in Unit.objects.filter(utype=unit_type):
		#    batches += Batch.objects.filter(unit_id=unit)
		# below returns avg x3 faster than above due to O(1) instead of O(n)
		try:
			return Batch.objects.filter(unit_id__utype=unit_type)
		except:
			return []
	
	def clean(self):
		'''
		Validate that the utype is defined by one of the enums in UnitType.
		'''
		if not Unit.has_unit_type_of_name(self.utype):
			raise ValidationError('\'Unit Type\' must match one of the pre-defined types.')


class Kit(models.Model):
	'''
	The boxed kit that a miniature(s) were obtained from.
	'''
	class Meta:
		verbose_name = 'Kit'
		verbose_name_plural = 'Kits'

	name = models.CharField(
		max_length=128,
		verbose_name='Kit Name')
	count = models.IntegerField(
		default=1,
		verbose_name='Kit Number')
	acqu_date = models.DateField(
		default=None,
		null=True,
		verbose_name='Acquisition Date'
	)
	

	def __str__(self):
		s = self.name
		if self.count > 1:
			s += '(%i)' % self.count
		return s
	
	# TODO bug - will only return one kit instead of many if multiple kits of the same
	# name exist. Need to expand it to be closer to something like Units.
	# if doing that, maybe make a new class that contains all helper methods to minimize repetition.

	def get_kit_via_name(kit_name):
		'''
		Get a reference of the kit by name if it exists, or None if it doesn't
		'''
		if kit_name == '':
			return None

		# get() throws an error if no hits, so catch it if no hits.
		try:
			return Kit.objects.get(name__icontains=kit_name)
		except:
			return None

	def get_batches_of_kit(self):
		'''
		Get a queryset of all batches that originated from this kit.
		'''
		return Batch.objects.filter(kit_id=self)
	

class Storage(models.Model):
	'''
	A physical container that holds miniatures. 
	'''
	class Meta:
		verbose_name = 'Storage'
		verbose_name_plural = 'Storage Containers'

	id = models.CharField(
		primary_key=True,
		max_length=32,
		verbose_name="Storage Tag")
	location = models.CharField(
		max_length=128, 
		verbose_name='Stored Location')
	last_moved = models.DateField(
		default=None, 
		null=True,
		verbose_name='Last Moved')
	
	class Capacity(models.IntegerChoices):
		EMPTY = 0, 'Empty'
		PARTIALY_FULL = 1, 'Partially-Full'
		HALF_FULL = 2, 'Half-Full'
		MOSTLY_FULL = 3, 'Mostly-Full'
		FULL = 4, 'Full'
	current_cap = models.IntegerField(
		choices=Capacity, 
		default=0)
	

	def __str__(self):
		return self.id

	def move_container(self, newLocation : str):
		'''
		Update the container's location and update it's last_moved date to today.
		'''
		self.location = newLocation
		self.last_moved = timezone.now().date()

	def can_increment_capacity(self):
		'''
		Check whether the capacity can be incremented or not.
		'''
		return 0 <= self.current_cap < 4
	
	def increment_capacity(self):
		'''
		Increment the current capacity.
		'''
		if not self.is_capacity_in_bounds():
			raise ValueError('Cannot increment capacity: current_cap is out of bounds')

		if self.can_increment_capacity():
			self.current_cap += 1

	def can_decrement_capacity(self):
		'''
		Check whether the capacity can be decremented or not.
		'''
		return 0 < self.current_cap <= 4
	
	def decrement_capacity(self):
		'''
		Decrement the current capacity.
		'''
		if not self.is_capacity_in_bounds():
			raise ValueError('Cannot decrement capacity: current_cap is out of bounds')

		if self.can_decrement_capacity():
			self.current_cap -= 1
		
	def is_full(self):
		'''
		Check whether the storage container is full or not.
		'''
		return self.current_cap == Storage.Capacity.FULL
	
	def is_capacity_in_bounds(self):
		'''
		Helper function to make sure current_cap is in range.
		'''
		return Storage.Capacity.EMPTY <= self.current_cap <= Storage.Capacity.FULL
	
	def get_stored_points(self):
		'''
		Get the point total from all Batches stored in this container.
		'''
		result = 0
		contents = Batch.objects.filter(storage_id=self.id)
		for batch in contents:
			result += batch.total_points()
		return result

	def get_capacity_string(self):
		'''
		Get the string representation of current_cap.
		'''
		return Storage.Capacity.choices[self.current_cap][1]

 
class Batch(models.Model):
	'''
	A single batch of miniatures that were built and painted together. Seperate from Units as some
	Units are large and can't be built/painted in one group.
	'''
	class Meta:
		verbose_name = 'Batch'
		verbose_name_plural = 'Batches'

	kit_id = models.ForeignKey(
		Kit, 
		on_delete=models.RESTRICT,
		verbose_name='Source Kit')
	unit_id = models.ForeignKey(
		Unit, 
		on_delete=models.RESTRICT,
		verbose_name='Representing Unit')
	storage_id = models.ForeignKey(
		Storage, 
		on_delete=models.RESTRICT,
		verbose_name='Current Storage')
	count = models.IntegerField(
		default=1, 
		verbose_name='Miniature Count')
	note = models.CharField(
		max_length=512, 
		default='',
		blank=True,
		verbose_name='Extra Note(s)')
	edit_date = models.DateField(
		default=None,
		null=True,
		verbose_name='Last Edited')
	
	class Stage(models.IntegerChoices):
		UNOPENED = 0, 'Unopened'
		BUILDING = 1, 'Building'
		MAGNETIZING = 2, 'Magnetizing'
		PRIMING = 3, 'Priming'
		PAINTING = 4, 'Painting'
		BASING = 5, 'Basing'
		VARNISHING = 6, 'Varnishing'
		REPAIRING = 7, 'Repairing'
		COMPLETED = 8, 'Completed'
		
	stage = models.IntegerField(
		choices=Stage,
		default=Stage.UNOPENED)


	def __str__(self):
		s = self.unit_id.name
		# If there are multiple Batches of this unit, add extra number based on acquisition date.
		collection = Batch.objects.filter(unit_id=self.unit_id).order_by('kit_id__acqu_date')
		if len(collection) > 1:
			for b in range(len(collection)):
				if collection[b].id == self.id:
					s += ' ' + (b+1).__str__()
		return s
	
	def __gt__(self, other):
		# use edit dates for comparisons
		if self.edit_date == other.edit_date:
			# if both edit dates are equal, use the string representation to compare instead. Do less
			# than so it better sorts in alphabetical order. 
			return self.__str__() <= other.__str__()
		else:
			return self.edit_date >= other.edit_date
		
	def __lt__(self, other):
		# as of now, default 'less than' are the least recently edited.
		return self.edit_date < other.edit_date
	
	def get_images(self):
		'''
		Get a list of all Batch Images, sorted with newest first.
		'''
		options = BatchImage.objects.filter(batch_id = self.id).order_by('-upload_date')
		if len(options) <= 0:
			return None
		else:
			return options
	
	def get_thumbnail_url(self):
		'''
		Get a single image, the newest, to use as a thumbnail.
		'''
		option = self.get_images()
		if option:
			return option[0].img_path.url
		else:
			return None
	
	def get_stage_string(self):
		'''
		Get the string representation of a Batch's Stage, or None if invalid.
		'''
		try:
			return Batch.Stage.choices[self.stage][1]
		except IndexError:
			return None

	def get_stage_via_name(stage_name):
		'''
		Get a stage enum val given a name if it exists, or None if it doesn't
		'''
		# dont bother if its too short, could cause too many false hits.
		if len(stage_name) <= 3:
			return None

		# make sure capitalization matches
		stage_name = stage_name.capitalize()
		all_stages = Batch.Stage.choices
		for pair in all_stages:
			# do startwith() to ensure partial matches hit as well
			if pair[1].startswith(stage_name):
				# return the num val
				return pair[0]
		else:
			return None

	def get_batches_of_stage(stage_type):
		'''
		Get a queryset of all batches that are at the given stage.
		'''
		try:
			temp = Batch.objects.filter(stage=stage_type)
			return temp
		except Exception as e:
			return []


	def total_points(self):
		'''
		Get the points total that this Batch represents.
		'''
		if self.unit_id:
			return self.count * self.unit_id.points
		else:
			return 0

	
class BatchImage(models.Model):
	'''
	A collection of images for Batches.
	'''
	class Meta:
		verbose_name = 'Batch Image'
		verbose_name_plural = 'Batch Images'

	img_path = models.ImageField(
		blank=False, 
		upload_to='uploads/',
		verbose_name='Image', 
		max_length=255)
	batch_id = models.ForeignKey(
		Batch,
		on_delete=models.CASCADE,
		verbose_name='Batch Image')
	upload_date = models.DateField(default=None,
		null=True,
		verbose_name='Upload Date')
	
	# const compression settings for image compression
	EXPORT_FILE_EXTENSION = '.jpg'
	MAX_RES = 2000
	RATIO = (3,4) # or (4:3) landscape
	COMPRESS_QUALITY = 85
	UPLOAD_LOCATION = 'uploads'


	def __str__(self):
		imgCount = BatchImage.objects.filter(batch_id=self.batch_id).order_by('id')
		# do a check to make sure its valid, otherwise it can break during a deletion
		if self.id is not None:
			imgCount = list(imgCount.values_list('id', flat=True)).index(self.id) + 1 
			return '%s img_%i' %(self.batch_id, imgCount)
		else:
			return 'img_data_not_found'


	def compress_image(self):
		'''
		Compress the image, assuming its not already compressed. 
		Returns whether or not the image was compressed.
		'''
		
		source = self.img_path.path
		# make a new image with desired compressions applied.
		original_img = Image.open(source)
		try:
			new_img = BatchImage.convert_image(original_img)
			original_img.close()
		except (ReferenceError, ValueError) as e:
			print(f'An error occured with opening the image file during compression: {str(e)}.')
			original_img.close()
			return False
			
		# save compressed variant and close image file
		export_name = os.path.splitext(source)[0] + self.EXPORT_FILE_EXTENSION
		new_img.save(export_name, optimize=True, quality=self.COMPRESS_QUALITY)
		new_img.close()
				
		# If the path was changed, then update the file path and delete the old image.
		if os.path.splitext(source)[1] != self.EXPORT_FILE_EXTENSION:
			if os.path.exists(source):
				os.remove(source)
			self.img_path.name = os.path.join( self.UPLOAD_LOCATION , export_name)
			self.save()

		#if settings.DEBUG:
		print(f'{self.img_path} compressed!')

		return True

	def is_image_compressed(image_path):
		'''
		Returns whether the saved image is already compressed or not.
		'''
		source = image_path
		
		# If this happens then its likely this object was corrupted, and needs to be investigated
		if not source or not os.path.isfile(source):
			if settings.DEBUG:
				print(f'The image file at {image_path} wasn\'t found. Please validate this '
						   + 'record in the database for corruption.')
			return None

		img_file = None
		try:
			img_file = Image.open(source)
		except (IOError, SyntaxError):
			if settings.DEBUG:
				print('Passed in file is not an image')
			return None

		# test if the file type
		if os.path.splitext(source)[1] != BatchImage.EXPORT_FILE_EXTENSION:
			return False
		
		# check if the largest dimension exceeds the max resolution
		img_max_dimension = max(img_file.width, img_file.height)
		if img_max_dimension > BatchImage.MAX_RES:
			return False

		# check if the actual ratio doesnt match with the desired ratio
		img_ratio = (round(img_file.width / img_max_dimension, 2) , round(img_file.height / img_max_dimension, 2))
		if img_ratio != BatchImage.get_working_ratio(img_file.width <= img_file.height):
			return False

		img_file.close()

		# At this point, every pass has been checked so return true
		return True

	def convert_image(opened_img : Image):
		'''
		Returns a new open Image with conversion modifiers applied, but not yet saved. 
		The original image pointer remains open after execution.
		Throws an ReferenceError if the image isnt open or valid.
		'''
		if not opened_img:
			raise ReferenceError('The passed in image to convert is invalid.')

		try: 
			# Generate new resolution that keeps orientation, but keeps it as large as possible without
			# extending its pixel count.
			is_portrait = opened_img.height >= opened_img.width
			working_ratio = BatchImage.get_working_ratio(is_portrait)
			tgt_res = min(BatchImage.MAX_RES, max(opened_img.width, opened_img.height))
			new_res = ( int(tgt_res * working_ratio[0]) , int(tgt_res * working_ratio[1]) )

			# generate new image based on original and apply conversions
			new_img = opened_img.convert('RGB')
			new_img = ImageOps.exif_transpose(new_img)
			new_img = ImageOps.fit(new_img, new_res)

			return new_img
		
		except ValueError:
			raise ReferenceError('The passed in image is not opened. Make sure to open it first before passing in.')

	def get_working_ratio(is_portrait : bool):
		'''
		Get a tuple of the working ratio, which are decimals that can multiply to 
		achieve the desired ratio. Ratio is (width, height).
		'''
		ratio_fraction = round(min(BatchImage.RATIO) / max(BatchImage.RATIO), 2)
		if is_portrait:
			# portrait ratio
			return ( ratio_fraction , 1 )
		else:
			# landscape ratio
			return ( 1, ratio_fraction )

	@mark_safe
	def img_tag(self):
		'''
		Get the HTML for a small thumbnail to use in the admin inline menu.
		'''
		return '<image src="%s" style="display: inline-block; object-fit: contain; height:150px; width:150px;"/>' % self.img_path.url
	img_tag.allow_tags = True
	img_tag.short_description = 'Image Thumbnail'

#region BatchImage Signals 
@receiver(pre_delete, sender=BatchImage, dispatch_uid='batchimage_delete_img')
def batchimage_delete_img(sender, instance, **kwargs):
	'''
	Before the BatchImage is deleted, delete the file it was connected to as well.
	'''
	#print('full delete called.')
	img_source = instance.img_path.path
	if os.path.isfile(img_source):
		os.remove(img_source)
		
@receiver(pre_save, sender=BatchImage, dispatch_uid='batchimage_delete_old')
def batchimage_delete_old(sender, instance, **kwargs):
	'''
	Before the BatchImage is saved, delete an old image if a new one was uploaded.
	'''
	try:
		old_img = BatchImage.objects.get(id=instance.id).img_path.path
	except BatchImage.DoesNotExist:
		return
	
	new_img = instance.img_path.path
	#print('An old image was found, deleting it.')

	if old_img != new_img:
		if os.path.isfile(old_img):
			os.remove(old_img)	

@receiver(post_save, sender=BatchImage, dispatch_uid='batchimage_try_compress')
def batchimage_try_compress(sender, instance, **kwargs):
	'''
	After the BatchImage is saved, try compressing the image.
	'''
	# dont call it its already compressed
	path = instance.img_path
	if not path or (BatchImage.is_image_compressed(path.path) == False):
		print('Compressing a new image.')
		instance.compress_image()

#endregion


class Tag(models.Model):
	'''
	A list of Tags defined in the database for unique queries. Multiple Tags can be assigned
	to multiple Batches unlike Categories.
	'''
	class Meta:
		verbose_name = 'Tag'
		verbose_name_plural = 'Tags'

	name = models.CharField(
		max_length=32,
		verbose_name='Tag')
	

	def __str__(self):
		return self.name
	
	def get_tag_via_name(tag_name):
		'''
		Get a tag reference by name if it exists, or None if it doesn't
		'''
		try:
			return Tag.objects.get(name=tag_name)
		except:
			return None
		
	def get_tagged_batches(self):
		'''
		Get a list of all Batches that have this tag
		'''
		batches = []
		for assign in TagAssignment.objects.filter(tag_id=self):
			batches.append(assign.batch_id)

		return batches


class TagAssignment(models.Model):
	'''
	Catalog of all assignemnts of tags to batches. This is the lookup table since Tags and Batches
	are a many-to-many relationship.
	'''
	class Meta:
		verbose_name = 'Tag'
		verbose_name_plural = 'Tag Assignments'

	tag_id = models.ForeignKey(
		Tag, 
		on_delete=models.RESTRICT,
		verbose_name='Tag')
	batch_id = models.ForeignKey(
		Batch,
		on_delete=models.CASCADE,
		verbose_name='Batch')
	

	def __str__(self):
		return "%s(%s)" % (self.batch_id, self.tag_id)