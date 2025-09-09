#pragma once

#include "ofxsImageEffect.h"
#include "ofxsMultiThread.h"

#include <memory>

class ColorFillPlugin : public OFX::ImageEffect {
public:
    ColorFillPlugin(OfxImageEffectHandle handle);
    virtual void render(const OFX::RenderArguments &args) override final;

private:
    // Do not need to delete these, the ImageEffect is managing them for us
    OFX::Clip *_dstClip;
    OFX::RGBAParam *_color;
};

// ColorFillPluginFactory will be declared by mDeclarePluginFactory macro
