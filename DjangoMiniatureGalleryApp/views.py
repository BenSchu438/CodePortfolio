from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic, View
from django.urls import reverse
from django.conf import settings
from django import forms

import time
from .models import *


def BatchIndexFunc(request):
    '''
    Batch Index view that will populate a list of Batches into a gallery. 
    It will either populate all items by default, or populate it based on search words.
    '''
    search_phrases = request.GET.get('search')
    search_hits = []
    batch_list = []
    start_time = time.time()

    if is_valid_search_string(search_phrases):
        search_phrases = parse_search_string(search_phrases)
        search_results = wide_db_search(search_phrases)
        batch_list = search_results[0]
        search_hits = search_results[1]
    else:
        batch_list = list(Batch.objects.all())

    # sort here
    # TODO - make other sorting filters here, but for now just default
    batch_list.sort(reverse=True)

    if settings.DEBUG:
        print("SEARCH TIME ELAPSED: " + (time.time() - start_time).__str__())

    # count all points in result for fun facts
    results_points = 0
    for b in batch_list:
        results_points += b.total_points()

    context = {
        'search_list': search_phrases,
        'batch_list': batch_list,
        'results_points': results_points,
        'search_hits': search_hits
    }
    return render(request, 'MiniatureGallery/batchindex.html', context)

def wide_db_search(search_terms):
    '''
    Get a list of batches, unsorted, that fit the passed in criteria
    '''
    if settings.DEBUG:
        print(search_terms)

    # store results in set. Intersect each continuous set to ensure 'AND' behavior
    output_set = set()
    # cache terms so we can skip repeat queries and print out 'hits' later
    terms = []

    for potential_tag in search_terms:
        # check each case, organized to do fastest checks first
        # TAG, CATEGORY, STAGE, KIT, UNIT_TYPE, UNIT_NAME
        # Majority of logic is contained in their appropriate model classes
        subsearch = set()

        # analyze each test, adding the first success possible

        if tag := Tag.get_tag_via_name(potential_tag):
            if tag.name in terms:
                continue
            terms.append(tag.name)
            subsearch = set( tag.get_tagged_batches() )

        elif category := Category.get_category_via_name(potential_tag):
            if category in terms:
                continue
            terms.append(category)
            subsearch = set( category.get_category_batches() )

        elif stage := Batch.get_stage_via_name(potential_tag):
            if stage in terms:
                continue
            terms.append(stage)
            subsearch = set( Batch.get_batches_of_stage(stage) )

        elif kit := Kit.get_kit_via_name(potential_tag):
            if kit.name in terms:
                continue
            terms.append(kit.name)
            subsearch = set( kit.get_batches_of_kit() )

        elif unit_type := Unit.get_unit_type_via_name(potential_tag):
            if unit_type in terms:
                continue
            terms.append(unit_type)
            subsearch = set( Unit.get_batches_of_unit_type(unit_type) )

        elif Unit.has_units_of_name(potential_tag):
            if potential_tag in terms:
                continue
            terms.append(potential_tag)
            subsearch = set( Unit.get_batches_with_unit_name(potential_tag) )
        

        # if nothing found in subsearch, move to next keyword
        if len(subsearch) == 0:
            continue
        # If an empty output_set, this was the first hit, so use all subsearch hits
        elif len(output_set) == 0:
            output_set = output_set.union(subsearch)
        # Otherwise, filter hits for 'AND' effect 
        else:
            output_set = output_set.intersection(subsearch)

    # return both hits and terms. Return terms for HTML bonuses
    return list(output_set), terms

def is_valid_search_string(tag_string : str):
    '''
    Check if a search string is valid to use in the search query.
    '''
    if tag_string is None:
        return False
    else:
        trimmed_str = tag_string.strip(" .,-_")
        return len(trimmed_str) > 0

def parse_search_string(tag_string : str):
    '''
    parse and format a long search string into a list of usable search terms.
    '''
    # clean string with uneccesary punctuation at the start/end
    new_list = tag_string.strip(" ,-_?/]}{[*\'")

    # format to be CSV with spaces allowed
    new_list = new_list.replace(" ", ",")
    new_list = new_list.replace("_", " ")

    # split into list
    new_list = new_list.split(",")
    return new_list


class BatchDetailView(generic.DetailView):
    '''
    Batch Details view that shows off the details for a single Batch object.
    '''
    model = Batch
    template_name= "MiniatureGallery/batchdetailv2.html"


class StorageIndexView(generic.ListView):
    '''
    Storage index view that shows off a list of storage containers to view.
    '''
    template_name = "MiniatureGallery/storageindex.html"
    context_object_name = "top_storage_list"

    def get_queryset(self):
        '''
        Get all storage containers sorted by ID
        '''
        # TODO - Make the table in storage index filterable
        return Storage.objects.order_by('id')


def StorageDetailFunc(request, storage_id):
    '''
    Storage detail view that shows off the storage's details as well as a gallery
    of all Batch objects stored within it.
    '''
    # get details of the question
    tag = get_object_or_404(Storage, pk=storage_id)

    # get stored models, load in for the gallery display
    stored_batches = Batch.objects.all().filter(
        storage_id=storage_id).order_by("unit_id__name")
    context = {
        'storage': tag,
        'batch_list': stored_batches,
        }
    return render(request, "MiniatureGallery/storagedetail.html", context)