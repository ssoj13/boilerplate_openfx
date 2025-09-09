#include "colorFill.h"
#include "ofxsImageEffect.h"
#include "ofxsMultiThread.h"
#include "ofxCore.h"
#include "ofxPixels.h"

#include <cstring>
#include <memory>
#include <algorithm>

using namespace OFX;

ColorFillPlugin::ColorFillPlugin(OfxImageEffectHandle handle)
    : ImageEffect(handle)
    , _dstClip(fetchClip(kOfxImageEffectOutputClipName))
    , _color(fetchRGBAParam("color"))
{}

void ColorFillPlugin::render(const OFX::RenderArguments &args)
{
    std::unique_ptr<OFX::Image> dst(_dstClip->fetchImage(args.time));
    if (!dst)
        throw std::runtime_error("Failed to fetch output image");

    const auto renderWindow = args.renderWindow;
    auto pixelData = static_cast<float*>(dst->getPixelData());
    const auto rowBytes = dst->getRowBytes();

    OfxRGBAColourD color;
    _color->getValueAtTime(args.time, color.r, color.g, color.b, color.a);

    for (int y = renderWindow.y1; y < renderWindow.y2; ++y)
    {
        float* dstPix = reinterpret_cast<float*>(
            static_cast<char*>(dst->getPixelData()) + y * rowBytes
        );

        for (int x = renderWindow.x1; x < renderWindow.x2; ++x)
        {
            dstPix[0] = static_cast<float>(color.r);
            dstPix[1] = static_cast<float>(color.g);
            dstPix[2] = static_cast<float>(color.b);
            dstPix[3] = static_cast<float>(color.a);
            dstPix += 4;
        }
    }
}

mDeclarePluginFactory(ColorFillPluginFactory, {}, {});

void ColorFillPluginFactory::describe(OFX::ImageEffectDescriptor &desc)
{
    desc.setLabels("ColorFill", "ColorFill", "Color Fill");
    desc.setPluginGrouping("Custom");
    desc.addSupportedContext(eContextFilter);
    desc.addSupportedContext(eContextGeneral);
    desc.addSupportedBitDepth(eBitDepthUByte);
    desc.addSupportedBitDepth(eBitDepthUShort);
    desc.addSupportedBitDepth(eBitDepthFloat);
    desc.setSingleInstance(false);
    desc.setHostFrameThreading(false);
    desc.setSupportsMultiResolution(true);
    desc.setSupportsTiles(true);
    desc.setTemporalClipAccess(false);
    desc.setRenderThreadSafety(eRenderFullySafe);
    desc.setSupportsMultipleClipPARs(false);
}

void ColorFillPluginFactory::describeInContext(OFX::ImageEffectDescriptor &desc, OFX::ContextEnum context)
{
    OFX::ClipDescriptor *dstClip = desc.defineClip(kOfxImageEffectOutputClipName);
    dstClip->addSupportedComponent(ePixelComponentRGBA);
    dstClip->setSupportsTiles(true);

    OFX::RGBAParamDescriptor *colorParam = desc.defineRGBAParam("color");
    colorParam->setLabels("Color", "Color", "Color");
    colorParam->setDefault(1.0, 1.0, 1.0, 1.0);
}

OFX::ImageEffect* ColorFillPluginFactory::createInstance(OfxImageEffectHandle handle, OFX::ContextEnum context)
{
    return new ColorFillPlugin(handle);
}

static ColorFillPluginFactory p("com.example.ColorFill", 1, 0);

namespace OFX 
{
    namespace Plugin 
    {
        void getPluginIDs(OFX::PluginFactoryArray &ids)
        {
            ids.push_back(&p);
        }
    }
}
