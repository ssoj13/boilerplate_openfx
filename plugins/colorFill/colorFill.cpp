// ColorFill — generator: fills the output with a constant (unpremultiplied) RGBA colour.
// Also usable as a filter; the Source input is ignored.

#include "ofxc/ofxc.h"

namespace {

const char *const kParamColor = "color";

template <class Fmt>
class FillProcessor : public OFX::ImageProcessor {
    using PIX = typename Fmt::Pix;

public:
    FillProcessor(OFX::ImageEffect &effect, const OfxRGBAColourD &color)
        : OFX::ImageProcessor(effect)
    {
        if constexpr (Fmt::nComponents == 1) {
            _pixel[0] = ofxc::toPixel<PIX, Fmt::maxValue>(color.a);
        } else {
            const double rgba[4] = {color.r, color.g, color.b, color.a};
            for (int c = 0; c < Fmt::nComponents; ++c)
                _pixel[c] = ofxc::toPixel<PIX, Fmt::maxValue>(rgba[c]);
        }
    }

    void multiThreadProcessImages(OfxRectI window) override
    {
        for (int y = window.y1; y < window.y2; ++y) {
            if (_effect.abort())
                return;
            auto *dst = static_cast<PIX *>(_dstImg->getPixelAddress(window.x1, y));
            for (int x = window.x1; x < window.x2; ++x, dst += Fmt::nComponents)
                std::copy(_pixel, _pixel + Fmt::nComponents, dst);
        }
    }

private:
    PIX _pixel[Fmt::nComponents];
};

class ColorFillPlugin : public OFX::ImageEffect {
public:
    explicit ColorFillPlugin(OfxImageEffectHandle handle)
        : ImageEffect(handle)
        , _dstClip(fetchClip(kOfxImageEffectOutputClipName))
        , _color(fetchRGBAParam(kParamColor))
    {}

    void render(const OFX::RenderArguments &args) override
    {
        auto dst = ofxc::fetchImage(_dstClip, args);
        OfxRGBAColourD color;
        _color->getValueAtTime(args.time, color.r, color.g, color.b, color.a);

        ofxc::dispatchPixelFormat(*dst, [&](auto fmt) {
            FillProcessor<decltype(fmt)> processor(*this, color);
            ofxc::runProcessor(processor, *dst, args);
        });
    }

    void getClipPreferences(OFX::ClipPreferencesSetter &prefs) override
    {
        prefs.setOutputPremultiplication(OFX::eImageUnPreMultiplied);
    }

private:
    // Owned by the ImageEffect, do not delete
    OFX::Clip *_dstClip;
    OFX::RGBAParam *_color;
};

} // namespace

mDeclarePluginFactory(ColorFillPluginFactory, {}, {});

void ColorFillPluginFactory::describe(OFX::ImageEffectDescriptor &desc)
{
    ofxc::describeCommon(desc, PLUGIN_LABEL, PLUGIN_GROUPING);
    desc.setPluginDescription("Fills the image with a constant colour.");
    desc.addSupportedContext(OFX::eContextGenerator);
    desc.addSupportedContext(OFX::eContextFilter);
    desc.addSupportedContext(OFX::eContextGeneral);
}

void ColorFillPluginFactory::describeInContext(OFX::ImageEffectDescriptor &desc, OFX::ContextEnum context)
{
    // Filter context mandates a "Source" clip; elsewhere it is optional. It is never read.
    OFX::ClipDescriptor *srcClip = desc.defineClip(kOfxImageEffectSimpleSourceClipName);
    srcClip->addSupportedComponent(OFX::ePixelComponentRGBA);
    srcClip->addSupportedComponent(OFX::ePixelComponentAlpha);
    srcClip->setSupportsTiles(true);
    srcClip->setOptional(context != OFX::eContextFilter);

    OFX::ClipDescriptor *dstClip = desc.defineClip(kOfxImageEffectOutputClipName);
    dstClip->addSupportedComponent(OFX::ePixelComponentRGBA);
    dstClip->addSupportedComponent(OFX::ePixelComponentAlpha);
    dstClip->setSupportsTiles(true);

    OFX::PageParamDescriptor *page = desc.definePageParam("Controls");

    OFX::RGBAParamDescriptor *color = desc.defineRGBAParam(kParamColor);
    color->setLabels("Color", "Color", "Color");
    color->setScriptName(kParamColor);
    color->setHint("Fill colour (unpremultiplied). Alpha-only outputs use the alpha component.");
    color->setDefault(1.0, 1.0, 1.0, 1.0);
    page->addChild(*color);
}

OFX::ImageEffect *ColorFillPluginFactory::createInstance(OfxImageEffectHandle handle, OFX::ContextEnum)
{
    return new ColorFillPlugin(handle);
}

OFXC_REGISTER_PLUGIN(ColorFillPluginFactory)
