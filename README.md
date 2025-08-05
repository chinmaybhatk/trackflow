# TrackFlow

Smart link tracking and attribution for Frappe CRM. Transform your CRM into a complete marketing attribution platform.

## Features

- **Smart Link Generation** - Create trackable short links with UTM parameters
- **Real-time Analytics** - Monitor clicks, conversions, and user journeys
- **CRM Integration** - Seamlessly link tracking data with leads, contacts, and deals
- **Multi-channel Attribution** - Track customer touchpoints across all marketing channels
- **ROI Measurement** - Connect marketing spend to revenue generation

## Requirements

- Frappe Framework v15.x
- Python 3.10+
- MariaDB 10.6+ or PostgreSQL 13+

## Installation

### From Frappe Bench

```bash
cd ~/frappe-bench
bench get-app https://github.com/chinmaybhatk/trackflow.git
bench --site your-site.local install-app trackflow
```

### For Development

```bash
cd ~/frappe-bench
bench get-app https://github.com/chinmaybhatk/trackflow.git --branch develop
bench --site your-site.local install-app trackflow
bench --site your-site.local set-config developer_mode 1
bench --site your-site.local clear-cache
```

## Configuration

After installation, navigate to:
**TrackFlow Settings** > **Setup**

Configure your tracking domain and preferences:
- Short domain configuration
- Default UTM parameters
- Link expiration settings
- Attribution models

## Quick Start

1. **Create a Campaign**
   - Go to `Marketing Campaign` list
   - Create new campaign with UTM parameters
   - Save and start generating links

2. **Generate Tracked Links**
   - Open any Lead/Contact/Deal
   - Click "Generate Tracked Link"
   - Share the generated short URL

3. **Monitor Performance**
   - Visit TrackFlow Dashboard
   - View real-time click data
   - Analyze conversion paths

## Documentation

For detailed documentation, visit our [Wiki](https://github.com/chinmaybhatk/trackflow/wiki)

## Support

- **Issues**: [GitHub Issues](https://github.com/chinmaybhatk/trackflow/issues)
- **Discussions**: [Community Forum](https://github.com/chinmaybhatk/trackflow/discussions)
- **Email**: support@trackflow.app

## Contributing

We welcome contributions! Please read our [Contributing Guide](CONTRIBUTING.md) first.

## License

MIT License. See [LICENSE](LICENSE) for more details.

---

Built with ❤️ for the Frappe community
