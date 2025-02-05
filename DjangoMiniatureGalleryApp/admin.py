from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from django import forms

from .models import *

#region INLINE CLASSES

class CategoryInline(admin.TabularInline):
    '''
    Category inline intended for easy access to 'subcategories' of a parent.
    '''

    model = Category
    fields = ['name', 'parent']

    extra = 0
    classes = ['collapse']

class UnitInline(admin.TabularInline):
    '''
    Unit inline to quickly view all Unit references an admin page may have.
    '''
    model = Unit
    fields = ['name']
    readonly_fields = ['name']

    extra = 0
    max_num = 0
    can_delete = False
    classes = ['collapse']

class BatchInline(admin.TabularInline):
    '''
    Batch inline to quickly view and go to all batch references an admin page may have.
    '''
    model = Batch
    fields = ['__str__', 'kit_id', 'stage', 'edit_date']
    readonly_fields = ['__str__', 'kit_id', 'stage', 'edit_date']

    extra = 0
    max_num = 0
    can_delete = False
    show_change_link = True
    classes = ['collapse']

class BatchImgInline(admin.TabularInline):
    '''
    Batch Img inline to view, edit, add, or delete an image from a batch.
    '''
    model = BatchImage
    extra = 0

    fields = ['img_path', 'img_tag', 'upload_date']
    readonly_fields = ['img_tag']

class TagAssignmentSeeBatchInline(admin.TabularInline):
    '''
    Tag Assignment inline that allows viewing the Batch only. Intended for the 'Tag' admin view.
    '''
    model = TagAssignment
    fields = ['batch_id']

    extra = 0
    can_delete = True
    classes = ['collapse']

class TagAssignmentSeeTagInline(admin.TabularInline):
    '''
    Tag Assignment inline that allows viewing the Tag only. Intended for the 'Batch' admin view.
    '''
    model = TagAssignment
    fields = ['tag_id']

    extra = 0
    can_delete = True
    classes = ['collapse']

#endregion 

#region ADMIN CLASSES

class CategoryAdmin(admin.ModelAdmin):
    '''
    Category Admin that allows naming a category, assigning a parent category, creating subcategories, 
    and viewing all units assigned the category.
    '''
    fields = ['name', 'parent']
    list_display = ['name', 'categorized_count', 'parent','is_category_safe']
    search_fields = ['name']
    ordering = ('parent', 'name')

    inlines = [CategoryInline, UnitInline]

    @admin.display(description='# of Units')
    def categorized_count(self, obj):
        '''
        Get the count of units assigned this category. 
        Has admin display settings for list_display.
        '''
        return (Unit.objects.filter(category=obj)).count()


class UnitAdmin(admin.ModelAdmin):
    '''
    Unit Admin that allows for naming and categorizing a unit, assigning it points, and 
    viewing/accessing Batches assigned it.
    '''
    fieldsets =  [
        ('Unit Info', {'fields': ['name', 'category', 'utype', 'points'],}),
    ]
    inlines = [BatchInline]

    list_display = ['name', 'category', 'utype', 'points']
    sortable_by = ['name', 'category', 'utype', 'points']
    search_fields = ['name', 'category__name', 'utype', 'points']


class KitAdmin(admin.ModelAdmin):
    '''
    Kit Admin that allows uploading new kits and viewing/accessing Batches that came from it.
    '''
    fields = ['name', 'count', 'acqu_date']
    list_display = ['__str__', 'unit_count', 'batch_count', 'acqu_date']
    search_fields = ['name']
    ordering = ['name', 'count', 'acqu_date']

    inlines = [BatchInline]

    @admin.display(description='# of Batches')
    def batch_count(self, obj):
        '''
        Get count of Batches that came from this kit.
        Has admin display settings for list_display.
        '''
        return (obj.get_batches_of_kit()).count()
    
    @admin.display(description='# of Units')
    def unit_count(self, obj):
        '''
        Get count of Units that came from this kit.
        Has admin display settings for list_display.
        '''
        batches = obj.get_batches_of_kit()
        units = []
        for b in batches:
            if b.unit_id not in units:
                units.append(b.unit_id)
        return len(units)


class StorageAdmin(admin.ModelAdmin):
    '''
    Storage Admin that allows for updating location of storage locations and capacity status.
    '''
    fields = ['id', 'location', 'current_cap','last_moved']
    list_display = ['id', 'location', 'current_cap','last_moved']
    search_fields = ['id', 'location', 'current_cap']
    ordering = ['-id', 'current_cap']

    inlines = [BatchInline]


class BatchAdmin(admin.ModelAdmin):
    '''
    Batch Admin that allows creation/edit of a Batch, as well as uploading Batch Images to a Batch.
    '''
    fieldsets =  [
        ('Model Info', {'fields': ['unit_id', 'count', 'total_points', 'kit_id'],}),
        ('Build Info', {'fields':[ 'stage', 'storage_id', 'note', 'edit_date'],}),
    ]
    readonly_fields=['edit_date', 'total_points']
    inlines = [BatchImgInline, TagAssignmentSeeTagInline]
    formfield_overrides = {
        models.CharField: {'widget': forms.Textarea },
    }

    list_display = ['get_sortable_string', 'kit_id', 'stage', 'edit_date']
    sortable_by = ['get_sortable_string', 'kit_id', 'stage', 'edit_date']
    search_fields = ['unit_id__name', 'kit_id__name', 'stage']

    
    def save_model(self, request, obj, form, change):
        '''
        When the model is saved, detect if a change was made. If so, set the edit date
        to today before continuing with the save.
        '''
        if change:
            obj.edit_date = timezone.now().date()
            obj.save()

        return super().save_model(request, obj, form, change)
    
    def save_formset(self, request, form, formset, change):
        '''
        When a form is saved, check Batch Images for changes, and update the 'upload date' to today
        for those that were edited/uploaded.
        '''
        instances = formset.save(commit=False)
        # make sure deleted items are removed
        for obj in formset.deleted_objects:
            obj.delete()
        for instance in instances:
            # if the instance edited is a batch image, update its upload date to today
            if type(instance) is BatchImage:
                instance.upload_date = timezone.now().date()
            instance.save()
        formset.save_m2m()
        
    @admin.display(description='Batch', ordering='unit_id__name')
    def get_sortable_string(self, obj):
        '''
        Get a string thats easily sortable.
        Has admin display settings for list_display. 
        '''
        return obj


class TagAdmin(admin.ModelAdmin):
    '''
    Tag Admin that allows for creating tags and assigning/revoking them from Batches.
    '''
    fields = ['name']
    list_display = ['name', 'count_tagged_batches']
    search_fields = ['name']

    inlines = [TagAssignmentSeeBatchInline]

    @admin.display(description='# of Tagged Batches')
    def count_tagged_batches(self, obj):
        '''
        Get number of Batches the tag is applied to. 
        Has admin display settings for list_display.
        '''
        return TagAssignment.objects.filter(tag_id=obj).count()
        
#endregion

admin.site.register(Category, CategoryAdmin)
admin.site.register(Unit, UnitAdmin)
admin.site.register(Kit, KitAdmin)
admin.site.register(Storage, StorageAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Tag, TagAdmin)
