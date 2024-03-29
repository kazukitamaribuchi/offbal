<!-- アプリサイドバー -->
<template>
    <div id="sidebar">
		<v-navigation-drawer
			v-model="drawer"
			:mini-variant="!drawer"
			permanent
			fixed
			hide-overlay
			class='main'
		>
            <!-- ハンバーガーメニュ -->
	    	<div class='pa-2 menu_open_btn_wrap'>
				<v-btn icon @click='togleDrawer'>
					<v-icon>mdi-menu</v-icon>
				</v-btn>
			</div>

            <!-- メニュー一覧 -->
			<v-list nav dense>
                <v-list-item
                    v-for="(menu, i) in menus"
                    :key='i'
                    @click='toPage(menu.route)'
                >
                    <v-list-item-icon>
                        <v-icon v-text='menu.icon'/>
                    </v-list-item-icon>
                    <v-list-item-title>{{ menu.title }}</v-list-item-title>
                </v-list-item>

                <!-- カテゴリー一覧 -->
                <draggable
                    :list='localCategories'
                    animation='200'
                    chosen-class="chosen"
                    drag-class="drag"
                    @end='end'
                >
                    <v-list-item
                        v-for="category in localCategories"
                        :key='category.id'
                        @click='toPage("DetailCategory", category)'
                    >
                        <v-list-item-icon>
                            <v-icon :color='category.color' v-text="category.icon"/>
                        </v-list-item-icon>
                        <v-list-item-title v-text="category.name"/>
                    </v-list-item>
                </draggable>
	 		</v-list>
		</v-navigation-drawer>

        <!-- モーダル読み込み -->
        <CreateLabelDialog
            ref='label'
        />

    </div>
</template>

<script>
    import CreateLabelDialog from '@/components/common/CreateLabelDialog'
    import draggable from 'vuedraggable'

    import { mapGetters, mapMutations } from 'vuex'
    import _ from 'lodash'
    import { Const } from '@/assets/js/const'
    const Con = new Const()

    export default {
        name: 'Sidebar',
        components: {
            CreateLabelDialog,
            draggable,
        },
        data () {
            return {
                drawer: true,
                menus: Con.SIDEBAR_MENU,
                local: [],
            }
        },
        created () {
        	this.localCategories = _.cloneDeep(this.categories)
        },
        watch: {
        	categories: {
        	    deep: true,
        	    handler (val, old) {
        	    	this.localCategories = _.cloneDeep(val)
        	    },
        	},
        },
    	computed: {
    		...mapGetters([
                'categories',
                'labels',
            ]),
            localCategories: {
                get () {
                    return this.local
                },
                set (val) {
                    this.local = val
                }
            },
    	},
        methods: {
            ...mapMutations([
               'updateCategoryIndex',
            ]),
            togleDrawer () {
                this.drawer = !this.drawer
                this.$emit('togleDrawer')
            },
            toPage (route, param) {
            	// カテゴリー or ラベルならparamを格納する
            	const params = param || ''
                // カテゴリ間の移動の判定
                if (this.$router.currentRoute.name === route) {
                    // カテゴリ名が違ったら移動する
                    if (param !== undefined && this.$router.currentRoute.params.name !== param.name) {
                        this.pagePush(route, params)
                    }
                // 異なるメニューへの移動の判定
                } else {
                    this.pagePush(route, params)
                }
                this.$eventHub.$emit('closeTaskDetail')
            },
            pagePush (route, params) {
                this.$router.push({
                    name: route,
                    params: {
                        name: params.name,
                    }
                })
                this.$eventHub.$emit('initCreateTaskField')
                this.$eventHub.$emit('initSort')
            },
            createLabel () {
                this.$refs.label.open()
            },
            end: _.debounce(function end (e) {
                this.$axios({
                    url: '/api/category/update_category_index/',
                    method: 'PUT',
                    data: {
                        categories: this.localCategories,
                    }
                })
                .then(res => {
                    console.log(res)
                    this.updateCategoryIndex(res.data)
                    this.$vs.notification({
                    	position: 'bottom-center',
                    	color: 'primary',
                    	buttonClose: false,
                    	classNotification: 'category_sort',
                    	text: 'カテゴリーの並び順を移動しました。'
                    })
                })
                .catch(e => {
                    console.log(e)
                })
            }, 1000),
        }
    }
</script>

<style lang="scss" scoped>
	.menu_open_btn_wrap > button {
		margin-left: 1px;
	}
    .v-list-group__items {
        .v-list-item {
            height: 40px;
        }
    }
    .chosen {
        opacity: 0.7;
        background: #03A9F4;
    }
    .drag {
        opacity: 0;
    }
    .v-expansion-panel--active > .v-expansion-panel-header {
        min-height: 40px;
    }

    .v-expansion-panel-header > *:not(.v-expansion-panel-header__icon) {
        flex: initial;
    }

    .v-expansion-panel-header::v-deep {
        min-height: 40px;
        justify-content: center;
        color: #777;
        transition: 0.3s all ease-in-out;

        &:hover {
            color: #333;

            &::before {
                opacity: 1 !important;
                background-color: #333;
            }
        }

        &::before {
            height: 1px;
            width: 100%;
            top: 50%;
            opacity: 1;
            background-color: #777;
        }

        .archived_title {
            position: relative;
            padding: 0 1em;
            display: inline-block;
            background-color: #fff;
            text-align: center;
            font-size: 14px;
        }
    }
</style>

<style lang='scss'>
    /* Vuesax通知パーツ用デザイン */
    .category_sort {
        .vs-notification__content__text p {
            color: #fff !important;
        }
    }
</style>
