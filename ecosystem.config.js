// PM2 配置文件 - AI Monitor 进程守护
module.exports = {
  apps: [
    {
      name: 'ai-monitor',
      script: 'uv',
      args: 'run -m src.main',
      cwd: '/data/data/com.termux/files/home/Projects/ai-monitor',
      interpreter: 'none',  // uv 是命令，不需要解释器

      // 日志配置
      log_file: './logs/pm2/combined.log',
      out_file: './logs/pm2/out.log',
      error_file: './logs/pm2/error.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      merge_logs: true,

      // 自动重启配置
      autorestart: true,
      watch: false,
      max_restarts: 20,  // 1小时内最大重启次数
      min_uptime: '10s',  // 最小运行时间，防止频繁重启
      restart_delay: 5000,  // 重启延迟（毫秒）

      // 内存限制（超过后自动重启）
      max_memory_restart: '500M',

      // 环境变量
      env: {
        TMPDIR: '$HOME/tmp',
        TEMP: '$HOME/tmp',
        TMP: '$HOME/tmp',
        GIT_TMPDIR: '$HOME/tmp',
        MONITOR_LOG_LEVEL: 'INFO',
        MONITOR_LOG_DIR: './logs',
        MONITOR_ALERT_IMAGE_DIR: './alerts',
        MONITOR_ENABLE_TERMUX_ALERTS: 'true',
        MONITOR_CAM_RECONNECT_ENABLED: 'true',
        MONITOR_CAM_TIMEOUT: '10.0',
      },

      // 生产环境配置
      env_production: {
        MONITOR_LOG_LEVEL: 'WARNING',
        MONITOR_LOG_MAX_BYTES: '10485760',  // 10 MB
        MONITOR_LOG_BACKUP_COUNT: '10',
      },
    },
  ],
};
