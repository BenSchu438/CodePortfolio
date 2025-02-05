from django.db import models
from django.contrib import admin
from django.conf import settings
from django.utils import timezone
from django.utils.safestring import mark_safe

import datetime

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
    
    def set_parent(self, new_parent):
        '''
        Set this category's new parent. Operation will cancel if it'd result in a loop.
        '''
        if new_parent:
            self.parent = new_parent
            if not self.is_category_safe():
                if settings.DEBUG:
                    print('Tried setting %s\'s parent to %s, but it makes a loop!'
                        % (self, new_parent))
                self.parent = None
            else:
                self.save()
        else:
            print('While setting a parent for %s, the new_parent could not be found' %(self))

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

    @admin.display(boolean=True, ordering="name", description="safe?")
    def is_category_safe(self):
        '''
        Check the category for any infinite loops in its heirarchy.
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
    
    def get_category_batches(self):
        '''
        Get a queryset of all batches from this Category and all subcategories.
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
        Get a queryset of all Batches that represent the Unit name given.
        '''
        return Batch.objects.filter(unit_id__name__icontains=unit_name)

    def get_batches_of_unit(self):
        '''
        Get a queryset of all Batches that this Unit represents.
        '''
        return Batch.objects.filter(unit_id=self)

    def get_unit_type_via_name(type_name):
        '''
        Get a reference of the UnitType Enum by name if it exists, or None if it doesn't
        '''
        try:
            u = Unit.objects.filter(utype=type_name).first()
            return u.utype
        except:
            return None

    def get_batches_of_unit_type(unit_type):
        '''
        Get queryset of all Batches that are assigned the given Unit Type Enum.
        '''
        #batches = []
        #for unit in Unit.objects.filter(utype=unit_type):
        #    batches += Batch.objects.filter(unit_id=unit)
        # below returns avg x3 faster than above due to O(1) instead of O(n)
        return Batch.objects.filter(unit_id__utype=unit_type)


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
    
    def get_kit_via_name(kit_name):
        '''
        Get a reference of the kit by name if it exists, or None if it doesn't
        '''
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
        # as of now, default 'geater than' are the most recently edited.
        if self.edit_date == other.edit_date:
            return self.__str__() >= other.__str__()
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
        Get the string representation of a Batch's Stage.
        '''
        return Batch.Stage.choices[self.stage][1]
    
    def get_stage_num(stage_name):
        '''
        Get a int of the Stage Enum by name if it exists, or None if it doesn't
        '''
        # dont bother if its too short
        if len(stage_name) < 3:
            return -1

        stage_name = stage_name.capitalize()
        all_stages = Batch.Stage.choices
        for pair in all_stages:
            if pair[1].startswith(stage_name):
                return pair[0]
        else:
            return -1

    def get_stage_via_name(stage_name):
        '''
        Get a stage enum by name if it exists, or None if it doesn't
        '''
        try:
            stage_num = Batch.get_stage_num(stage_name)
            u = Batch.objects.filter(stage=stage_num).first()
            return u.stage
        except:
            return None

    def get_batches_of_stage(stage_type):
        '''
        Get a queryset of all batches that are at the given stage.
        '''
        return Batch.objects.filter(stage=stage_type)

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
        verbose_name='Image')
    batch_id = models.ForeignKey(
        Batch,
        on_delete=models.CASCADE,
        verbose_name='Batch Image')
    upload_date = models.DateField(default=None,
        null=True,
        verbose_name='Upload Date')
    
    def __str__(self):
        imgCount = BatchImage.objects.filter(batch_id=self.batch_id).order_by('id')
        # do a check to make sure its valid, otherwise it can break during a deletion
        if self.id is not None:
            imgCount = list(imgCount.values_list('id', flat=True)).index(self.id) + 1 
            return '%s img_%i' %(self.batch_id, imgCount)
        else:
            return '%s %s' %(self.batch_id, self.img_path.file)

    @mark_safe
    def img_tag(self):
        '''
        Get the HTML for a small thumbnail to use in the admin inline menu.
        '''
        return '<image src="%s" style="display: inline-block; object-fit: contain; height:150px; width:150px;"/>' % self.img_path.url
    img_tag.allow_tags = True
    img_tag.short_description = 'Image Thumbnail'


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
            return Tag.objects.get(name__icontains=tag_name)
        except:
            return None
        
    def get_tagged_batches(self):
        '''
        Get a queryset of all Batches that have this tag
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