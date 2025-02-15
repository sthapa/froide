<template>
  <div class="document mb-3">
    <div class="card">
      <div
        ref="top"
        class="card-header"
      >
        {{ i18n._('newDocumentPageCount', {count: numPages} ) }}
      </div>
      <div
        class="card-body"
        :class="{'is-new': document.new}"
      >
        <div
          v-if="converting"
          class="progress"
        >
          <div
            class="progress-bar"
            :class="{'progress-bar-animated progress-bar-striped': progressCurrent === null}"
            :style="{'width': progressCurrent ? progressCurrent : '100%'}"
            role="progressbar"
            :aria-valuenow="progressCurrent ? progressCurrent : 0"
            aria-valuemin="0"
            aria-valuemax="100"
          />
        </div>
        <div v-else>
          <p class="text-muted">
            {{ i18n.imageDocumentExplanation }} 
          </p>
          <div class="form-group">
            <label for="page-label">{{ i18n.attachmentName }}</label>
            <input
              v-model="documentName"
              type="text"
              class="form-control"
              :placeholder="i18n.documentTitlePlaceholder"
            >
          </div>
          <draggable
            v-model="pages"
            class="row pages bg-light"
            @start="drag=true"
            @end="drag=false"
          >
            <image-page
              v-for="page in pages"
              :key="page.pageNum"
              :page="page"
              :page-count="pages.length"
              @pageupdated="$emit('pageupdated', {document, ...$event})"
              @splitpages="splitPages"
            />
          </draggable>
        </div>
        <div class="row mt-3">
          <div class="col-md-12">
            <p class="text-right">
              <button
                class="btn btn-primary mt-2"
                :disabled="anyUploads || converting"
                @click="convertImages"
              >
                {{ i18n.convertImages }}
              </button>
              <file-review
                :config="config"
                :document="document"
                @docupdated="updateDocument"
              />
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>

import draggable from 'vuedraggable'

import ImagePage from './image-page.vue'
import FileReview from './file-review.vue'

import I18nMixin from '../../lib/i18n-mixin'
import {DocumentMixin} from './lib/document_utils'

import {postData} from '../../lib/api.js'

export default {
  name: 'ImageDocument',
  components: {
    draggable,
    ImagePage,
    FileReview,
  },
  mixins: [I18nMixin, DocumentMixin],
  props: {
    config: {
      type: Object,
      required: true
    },
    document: {
      type: Object,
      required: true
    }
  },
  data () {
    return {
      progressTotal: null,
      progressCurrent: null,
      converting: false,
    }
  },
  computed: {
    numPages () {
      return this.pages.length
    },
    pages: {
      get: function() {
        return this.document.pages
      },
      set: function (pages) {
        this.$emit('pageschanged', pages)
      }
    },
    documentName: {
      get: function() {
        return this.document.name
      },
      set: function (name) {
        this.$emit('namechanged', name)
      }
    },
    anyUploads () {
      return !this.pages.every((p) => {
        return p && p.id
      })
    },
  },
  mounted () {
    if (this.document.new) {
      window.setTimeout(() => this.$emit('notnew'), 2000);
    }
  },
  methods: {
    splitPages (pageNum) {
      this.$emit('splitpages', pageNum)
    },
    convertImages () {
      this.converting = true
      this.$refs.top.scrollIntoView(true)
      let data = {
        action: 'convert_to_pdf',
        title: this.document.name,
        images: this.pages.map((p) => {
          return {
            id: p.id,
            rotate: (p.rotate || 0) + (p.implicitRotate || 0)
          }
        })
      }
      postData(
        this.$root.url.convertAttachments,
        data,
        this.$root.csrfToken
      ).then((attachment) => {
        this.$emit('imagesconverted', {
          attachment: attachment,
          imageDoc: this.document
        })
      })
    }
  }
}
</script>

<style lang="scss" scoped>
  .pages {
    display: flex;
    flex-wrap: nowrap;
    align-items: baseline;
    overflow: auto;
    overflow-x: scroll;
    overflow-scrolling: touch;
    padding-bottom: 2rem;
  }

</style>
