from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.views import generic, View
from django.urls import reverse
from django.conf import settings
from django import forms

import time
from .models import *
from .searches import *

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
    
    # send data and stats to HTML
    context = {
        'search_list': search_phrases,
        'batch_list': batch_list,
        'search_hits': search_hits,
    }
    context.update( get_gallery_context_stats(batch_list) )

    return render(request, 'MiniatureGallery/batchindex.html', context)


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
    context.update( get_gallery_context_stats(stored_batches) )
    return render(request, "MiniatureGallery/storagedetail.html", context)