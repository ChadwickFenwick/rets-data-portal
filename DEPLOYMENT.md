# Railway Deployment Guide

## Quick Deploy to Railway

1. **Connect Repository to Railway**
   - Go to [Railway.app](https://railway.app)
   - Create a new project
   - Connect your GitHub repository
   - Railway will automatically detect the Dockerfile and deploy

2. **Environment Variables (Optional)**
   Set these in Railway dashboard if you need to customize:
   ```
   PORT=8080 (Railway sets this automatically)
   STREAMLIT_SERVER_PORT=8080
   STREAMLIT_SERVER_ADDRESS=0.0.0.0
   STREAMLIT_SERVER_HEADLESS=true
   ```

3. **Custom Domain (Optional)**
   - In Railway dashboard, go to Settings
   - Add a custom domain if needed
   - Railway provides a default domain automatically

## Files Created for Deployment

- **Dockerfile**: Containerizes the application
- **railway.toml**: Railway-specific configuration
- **requirements.txt**: Python dependencies
- **health.py**: Health check endpoint for monitoring
- **.gitignore**: Excludes unnecessary files from deployment

## Deployment Features

✅ **Auto-scaling**: Railway handles traffic spikes automatically  
✅ **Health checks**: Built-in monitoring endpoint  
✅ **Zero-downtime deployments**: Rolling updates  
✅ **Automatic HTTPS**: SSL certificates handled by Railway  
✅ **Environment management**: Secure environment variables  

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally (matches Railway configuration)
streamlit run app_new.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true

# Test health check
curl http://localhost:8080?health=true
```

## Monitoring

Railway provides:
- Application logs
- Resource usage metrics
- Deployment status
- Custom health check endpoint at `/health`

## Cost Optimization

Railway offers:
- **Hobby Plan**: Free tier with limitations
- **Pro Plan**: $5/month per seat
- **Usage-based pricing**: Pay only for what you use

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Review build logs in Railway dashboard

2. **Runtime Errors**
   - Check application logs in Railway
   - Verify environment variables
   - Test locally with same configuration

3. **Connection Issues**
   - Ensure port 8080 is used
   - Check firewall rules for RETS servers
   - Verify external API access

### Performance Tips

1. **Memory Usage**: Monitor memory consumption in Railway dashboard
2. **Response Time**: Use Railway's built-in metrics
3. **Database**: Consider adding persistent storage for large datasets
4. **Caching**: Implement Redis for session data if needed

## Next Steps

After successful deployment, consider:
- Setting up custom domain
- Configuring monitoring alerts
- Adding authentication system
- Implementing data persistence
- Setting up automated backups