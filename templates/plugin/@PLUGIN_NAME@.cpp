// @PLUGIN_LABEL@ — filter: multiplies the colour channels of Source by a gain (alpha untouched).
// Generated from templates/plugin by `bootstrap.py new`. Replace the processor with your algorithm.

#include "ofxc/ofxc.h"

namespace {

const char *const kParamGain = "gain";

template <class Fmt>
class @PLUGIN_CLASS@Processor : public OFX::ImageProcessor {
    using PIX = typename Fmt::Pix;
    static constexpr int nComps = Fmt::nComponents;

public:
    @PLUGIN_CLASS@Processor(OFX::ImageEffect &effect, const OFX::Image *src, double gain)
        : OFX::ImageProcessor(effect)
        , _src(src)
        , _gain(gain)
    {}

    void multiThreadProcessImages(OfxRectI window) override
    {
        for (int y = window.y1; y < window.y2; ++y) {
            if (_effect.abort())
                return;
            auto *dst = static_cast<PIX *>(_dstImg->getPixelAddress(window.x1, y));
            for (int x = window.x1; x < window.x2; ++x, dst += nComps) {
                // Source may not cover the whole render window (multi-resolution): black outside it
                const auto *src = _src ? static_cast<const PIX *>(_src->getPixelAddress(x, y)) : nullptr;
                if (!src) {
                    std::fill(dst, dst + nComps, PIX(0));
                    continue;
                }
                for (int c = 0; c < nComps; ++c) {
                    const bool isAlpha = (nComps == 1) || (nComps == 4 && c == 3);
                    dst[c] = isAlpha ? src[c]
                                     : ofxc::toPixel<PIX, Fmt::maxValue>(
                                           ofxc::fromPixel<PIX, Fmt::maxValue>(src[c]) * _gain);
                }
            }
        }
    }

private:
    const OFX::Image *_src;
    double _gain;
};

class @PLUGIN_CLASS@Plugin : public OFX::ImageEffect {
public:
    explicit @PLUGIN_CLASS@Plugin(OfxImageEffectHandle handle)
        : ImageEffect(handle)
        , _srcClip(fetchClip(kOfxImageEffectSimpleSourceClipName))
        , _dstClip(fetchClip(kOfxImageEffectOutputClipName))
        , _gain(fetchDoubleParam(kParamGain))
    {}

    void render(const OFX::RenderArguments &args) override
    {
        auto dst = ofxc::fetchImage(_dstClip, args);
        auto src = ofxc::fetchImage(_srcClip, args, /*optional=*/true);
        if (src && (src->getPixelDepth() != dst->getPixelDepth() ||
                    src->getPixelComponents() != dst->getPixelComponents())) {
            OFX::throwSuiteStatusException(kOfxStatErrImageFormat);
        }
        const double gain = _gain->getValueAtTime(args.time);

        ofxc::dispatchPixelFormat(*dst, [&](auto fmt) {
            @PLUGIN_CLASS@Processor<decltype(fmt)> processor(*this, src.get(), gain);
            ofxc::runProcessor(processor, *dst, args);
        });
    }

    bool isIdentity(const OFX::IsIdentityArguments &args, OFX::Clip *&identityClip, double &identityTime) override
    {
        if (_gain->getValueAtTime(args.time) != 1.0)
            return false;
        identityClip = _srcClip;
        identityTime = args.time;
        return true;
    }

private:
    // Owned by the ImageEffect, do not delete
    OFX::Clip *_srcClip;
    OFX::Clip *_dstClip;
    OFX::DoubleParam *_gain;
};

} // namespace

mDeclarePluginFactory(@PLUGIN_CLASS@PluginFactory, {}, {});

void @PLUGIN_CLASS@PluginFactory::describe(OFX::ImageEffectDescriptor &desc)
{
    ofxc::describeCommon(desc, PLUGIN_LABEL, PLUGIN_GROUPING);
    desc.setPluginDescription("Multiplies colour channels by a gain.");
    desc.addSupportedContext(OFX::eContextFilter);
    desc.addSupportedContext(OFX::eContextGeneral);
}

void @PLUGIN_CLASS@PluginFactory::describeInContext(OFX::ImageEffectDescriptor &desc, OFX::ContextEnum)
{
    OFX::ClipDescriptor *srcClip = desc.defineClip(kOfxImageEffectSimpleSourceClipName);
    srcClip->addSupportedComponent(OFX::ePixelComponentRGBA);
    srcClip->addSupportedComponent(OFX::ePixelComponentAlpha);
    srcClip->setSupportsTiles(true);

    OFX::ClipDescriptor *dstClip = desc.defineClip(kOfxImageEffectOutputClipName);
    dstClip->addSupportedComponent(OFX::ePixelComponentRGBA);
    dstClip->addSupportedComponent(OFX::ePixelComponentAlpha);
    dstClip->setSupportsTiles(true);

    OFX::PageParamDescriptor *page = desc.definePageParam("Controls");

    OFX::DoubleParamDescriptor *gain = desc.defineDoubleParam(kParamGain);
    gain->setLabels("Gain", "Gain", "Gain");
    gain->setScriptName(kParamGain);
    gain->setHint("Multiplier for the colour channels.");
    gain->setDefault(1.0);
    gain->setRange(0.0, 100.0);
    gain->setDisplayRange(0.0, 4.0);
    gain->setIncrement(0.01);
    gain->setDoubleType(OFX::eDoubleTypeScale);
    page->addChild(*gain);
}

OFX::ImageEffect *@PLUGIN_CLASS@PluginFactory::createInstance(OfxImageEffectHandle handle, OFX::ContextEnum)
{
    return new @PLUGIN_CLASS@Plugin(handle);
}

OFXC_REGISTER_PLUGIN(@PLUGIN_CLASS@PluginFactory)
