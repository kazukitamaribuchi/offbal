<template>
    <vs-dialog v-model="localTaskDialog" width="600px">
        <v-container
            fluid
            class="task_dialog_wrap"
        >
            <h5
                class="task_dialog_header"
                align="center"
            >
                新規タスクを追加
            </h5>
            <ValidationObserver ref="task" v-slot="{ invalid }">
                <v-row
                    class="task_dialog_task_area_wrap"
                >
                    <v-col
                        cols="11"
                        class="task_dialog_task_input_area"
                    >
                        <ValidationProvider name='タスク' rules="required|max:100">
                            <v-textarea
                                class="mt-3"
                                outlined
                                label="例: 英単語、プログラミング、ブログ、読書"
                                v-model="task.content"
                                rows="5"
                                no-resize
                                :counter="100"
                            >
                            </v-textarea>
                        </ValidationProvider>
                    </v-col>
                    <v-col
                        cols="1"
                        class="task_dialog_btn_area"
                    >
                        <StartTimeBtn/>
                        <DeadLineBtn/>
                        <CategoryBtn
                            :defaultCategoryId=detailCategory.id
                        />
                        <LabelBtn/>
                        <PriorityBtn/>
                        <ReminderBtn/>
                    </v-col>
                </v-row>
                <v-row>
                    <v-col
                        cols="9"
                    >
                        <vs-input
                            class="mt-1"
                            v-model="task.comment"
                            placeholder="コメント"
                        >
                            <template #icon>
                                <v-icon
                                    color="teal accent-3"
                                >mdi-comment-outline</v-icon>
                            </template>
                        </vs-input>
                    </v-col>
                    <v-col
                        cols="3"
                    >
                        <vs-button
                            relief
                            color="#40e0d0"
                            :disabled="invalid"
                            @click.prevent="addLocalTask"
                        >
                            タスクを追加
                            <template #animate>
                                <i class="bx bxs-paper-plane"></i> 送信
                            </template>
                        </vs-button>
                    </v-col>
                </v-row>
            </ValidationObserver>
        </v-container>
    </vs-dialog>
</template>
<script>
    import { mapGetters, mapMutations } from 'vuex'
    import StartTimeBtn from '@/components/parts/StartTimeBtn'
    import DeadLineBtn from '@/components/parts/DeadLineBtn'
    import CategoryBtn from '@/components/parts/CategoryBtn'
    import LabelBtn from '@/components/parts/LabelBtn'
    import PriorityBtn from '@/components/parts/PriorityBtn'
    import ReminderBtn from '@/components/parts/ReminderBtn'

    export default {
        name: 'TaskDialog',
        components: {
            StartTimeBtn,
            DeadLineBtn,
            CategoryBtn,
            LabelBtn,
            PriorityBtn,
            ReminderBtn,
        },
        props: {
            taskDialog: {
                type: Boolean,
                required: true
            }
        },
        data: () => ({
            task: {
                category_id: 0,
                content: '',
                comment: '',
                start_time_str: '',
                deadline_str: '',
                remind_str: '',
                priority: '1',
                label_list: [],
            },
        }),
        created () {
            this.$eventHub.$off('createTaskInfo', this.createTaskInfo)
            this.$eventHub.$on('createTaskInfo', this.createTaskInfo)
        },
        mounted: function () {
        },
        watch: {},
        computed: {
            localTaskDialog: {
                get: function () {
                    this.init()
                    return this.taskDialog
                },
                set: function (value) {
                    this.init()
                    this.$emit('update', value)
                },
            },
            ...mapGetters([
                'detailCategory',
            ])
        },
        methods: {
            ...mapMutations([
                'addTask',
            ]),
            addLocalTask () {
                console.log('タスクを追加')
                console.log(this.task)
                this.$axios({
                    url: '/api/task/',
                    method: 'POST',
                    data: this.task,
                })
                .then(res => {
                    console.log(res)
                    const category = res.data.target_category_name
                    if (this.$route.path !== `/myapp/category/${category}`) {
                        this.$router.push({
                            path: `/myapp/category/${category}`
                        })
                    }
                    this.addTask(res.data)
                })
                .catch(e => {
                    console.log(e)
                })
                this.localTaskDialog = false
                this.init()
            },
            createTaskInfo (key, value) {
                this.task[key] = value
            },
            init () {
                this.task = {
                    category_id: 0,
                    content: '',
                    comment: '',
                    start_time_str: '',
                    deadline_str: '',
                    remind_str: '',
                    priority: '1',
                    label_list: [],
                }
            }
        },
    }

</script>
<style lang='scss' scoped>
    .task_dialog_wrap {
        height: 300px;
        .task_dialog_task_area_wrap {
            height: 185px;
            margin-bottom: 30px;
        }
        .task_dialog_task_input_area {
            height: 100%;
        }
        .vs-input-parent::v-deep {
            width: 100%;
            .vs-input {
                width: 100%;
            }
        }
        .task_dialog_btn_area {
            position: relative;
            top: -15px;
        }
    }
</style>
