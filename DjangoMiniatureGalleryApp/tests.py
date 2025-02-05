from django.test import TestCase
from django.utils import timezone
import datetime

from .models import Storage, Category

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
        #A's parent is now F, now theres a cycle
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

    #region set_parent
    def test_set_parent_with_safe_category(self):
        '''
        set_parent(new_parent) should be able to set a valid parent if no loops are made
        '''
        a = Category(name='A')
        b = Category(name='B')
        a.save()
        b.save()

        b.set_parent(a)

        self.assertIs(b.parent, a)
        
    def test_set_parent_with_loop(self):
        '''
        set_parent(new_parent) should undo any loop it tries to create
        '''
        a = Category(name='A')
        b = Category(name='B')
        a.save()
        b.save()

        b.set_parent(a)
        a.set_parent(b)

        self.assertIs(a.parent, None)
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