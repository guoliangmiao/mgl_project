# borker 的配置信息,通过这个配置信息我们可以将消息队列的信息保存在 redis的14号库中
# broker_url = "redis://127.0.0.1/14"
# #执行的结果保存在 redis的15号库中
# result_backend = "redis://127.0.0.1/15"

broker_url= 'amqp://guest:guest@127.0.0.1:5673'