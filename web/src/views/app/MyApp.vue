<template>
    <div id='my-app'>
        <MyAppHeader/>
        <v-container fluid>
            <v-row>
           		<Sidebar
           			@togleDrawer='drawer = !drawer'
           		/>
                <v-col cols='12' class='myapp_main_wrap main' :class="{ 'is-drawer': drawer }">
                    <router-view/>
                </v-col>
            </v-row>
        </v-container>
    </div>
</template>

<script>
    import MyAppHeader from '@/components/common/MyAppHeader'
    import Sidebar from '@/components/common/Sidebar'

    import { mapGetters, mapActions } from 'vuex'

    export default {
        name: 'MyApp',
        components: {
            MyAppHeader,
            Sidebar,
        },
        data: () => ({
            drawer: true,
        }),
        created () {
        	this.appInitAction()
        	.then(res => {
                // 何もしない
                this.setTheme(this, res.data.setting)
        	})
        	.catch(e => {
                console.log(e.response)
                // 初期データが作成されてないので、作成画面へ
        		if (!e.response.data.result) this.$router.push('/init-select-category')
            })
        },
        computed: {
            ...mapGetters('setting', [
                'setting',
            ])
        },
        methods: {
            ...mapActions([
            	'appInitAction',
            ]),
        },
    }
</script>

<style lang="scss" scoped>
    .myapp_main_wrap {
        margin-left: 60px;
        max-width: calc(100% - 60px);
    	position: relative;
        transition: .2s;
        transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
        z-index: 1;
    }
    .is-drawer {
        margin-left: 256px;
        max-width: calc(100% - 256px);
    }
</style>
